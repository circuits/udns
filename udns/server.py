#!/usr/bin/env python


from __future__ import print_function


import sys
import logging
from time import sleep
from os import environ
from logging import getLogger
from socket import AF_INET, SOCK_STREAM, socket
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter, FileType


from cachetools import LRUCache

from dnslib import DNSQuestion, DNSRecord
from dnslib import CLASS, QR, QTYPE, RDMAP, RR

from redisco.models import Model
from redisco import connection_setup, get_client
from redisco.models import Attribute, IntegerField, ListField


from circuits.app import Daemon
from circuits.net.events import write
from circuits.net.sockets import UDPServer
from circuits import Component, Debugger, Event, Timer


__version__ = "0.0.1"


class request(Event):
    """request Event"""


class response(Event):
    """response Event"""


class Zone(Model):

    name = Attribute(required=True, unique=True)
    ttl = IntegerField(default=0)
    records = ListField("Record")

    def delete(self):
        for record in self.records:
            record.delete()
        super(Zone, self).delete()

    def _add_record(self, rname, rdata, rclass=CLASS.IN, rtype=QTYPE.A, ttl=0):
        record = Record(
            rname=rname, rdata=rdata,
            rclass=rclass, rtype=rtype, ttl=ttl
        )
        record.save()
        self.records.append(record)
        self.save()

    def add_record(self, rname, rdata, **options):
        rclass = options.get("rclass", CLASS.IN)
        rtype = options.get("rtype", QTYPE.A)
        ttl = options.get("ttl", self.ttl)

        rclass = rclass if rclass is not None else CLASS.IN
        rtype = rtype if rtype is not None else QTYPE.A
        ttl = ttl if ttl is not None else self.ttl

        self._add_record(
            "{0:s}.{1:s}".format(rname, self.name), rdata,
            rclass=rclass, rtype=rtype, ttl=ttl
        )

    def delete_record(self, rname):
        fullname = "{0:s}.{1:s}".format(rname, self.name)
        records = [
            (i, record)
            for i, record in enumerate(self.records)
            if record.rname == fullname
        ]

        if not records:
            return

        i, record = records[0]
        record.delete()

        del self.records[i]
        self.save()

    def load(self, filename):
        fd = sys.stdin if filename == "-" else open(filename, "r")
        for rr in RR.fromZone(fd.read()):
            rname = str(rr.rname)
            rdata = str(rr.rdata)
            rclass = rr.rclass
            rtype = rr.rtype
            ttl = rr.ttl

            self._add_record(rname, rdata, rclass=rclass, rtype=rtype, ttl=ttl)

    def export(self):
        out = [
            "$TTL {0:d}".format(self.ttl),
            "$ORIGIN {0:s}".format(self.name.rstrip(".")),
            "",
        ]

        for record in self.records:
            rr = record.rr
            rname = rr.rname.stripSuffix(self.name).label[0]
            out.append(
                "{0:23s} {1:7d} {2:7s} {3:7s} {4:s}".format(
                    rname, rr.ttl,
                    CLASS.get(rr.rclass),
                    QTYPE.get(rr.rtype),
                    rr.rdata.toZone()
                )
            )

        return "\n".join(out)

    class Meta:
        indicies = ("id", "name",)


class Record(Model):

    rname = Attribute(required=True)
    rdata = Attribute(required=True)

    ttl = IntegerField(default=0)

    rclass = IntegerField(default=CLASS.IN)
    rtype = IntegerField(default=QTYPE.A)

    @property
    def rr(self):
        rdata = RDMAP[QTYPE[self.rtype]](self.rdata)
        return RR(self.rname, self.rtype, self.rclass, self.ttl, rdata)

    class Meta:
        indicies = ("id", "rname", "rclass", "rtype", "ttl", "rdata",)


class DNS(Component):

    def read(self, peer, data):
        record = DNSRecord.parse(data)
        event = request if record.header.qr == QR.QUERY else response
        return self.fire(event(peer, record))


class Server(Component):

    def init(self, args, db, logger):
        self.args = args
        self.db = db

        self.logger = logger

        self.bind = args.bind
        self.forward = args.forward

        self.peers = {}
        self.requests = {}
        self.cache = LRUCache(maxsize=100)

        if args.daemon:
            Daemon(args.pidfile).register(self)

        if args.debug:
            Debugger(events=args.verbose, logger=logger).register(self)

        self.transport = UDPServer(self.bind).register(self)
        self.protocol = DNS().register(self)

    def ready(self, server, bind):
        self.logger.info(
            "DNS Server Ready! Listening on {0:s}:{1:d}".format(*bind)
        )

        Timer(1, Event.create("ttl"), persist=True).register(self)

    def ttl(self):
        for k, rrs in self.cache.items():
            for rr in rrs[:]:
                if rr.ttl == 0:
                    rrs.remove(rr)
                    if not rrs:
                        del self.cache[k]
                else:
                    rr.ttl -= 1

    def request(self, peer, request):
        qname = request.q.qname
        qtype = request.q.qtype
        qclass = request.q.qclass

        key = (qname, qtype, qclass)
        if key in self.cache:
            self.logger.info(
                "Cached Request ({0:s}): {1:s} {2:s} {3:s}".format(
                    "{0:s}:{1:d}".format(*peer),
                    CLASS.get(qclass), QTYPE.get(qtype), qname
                )
            )

            reply = request.reply()
            for rr in self.cache[key]:
                reply.add_answer(rr)
            self.fire(write(peer, reply.pack()))
            return

        records = Record.objects.filter(
            rname=qname, rclass=qclass, rtype=qtype
        )

        if records:
            self.logger.info(
                "Authoritative Request ({0:s}): {1:s} {2:s} {3:s}".format(
                    "{0:s}:{1:d}".format(*peer),
                    CLASS.get(qclass), QTYPE.get(qtype), qname
                )
            )

            rr = [record.rr for record in records]
            reply = request.reply()
            reply.add_answer(*rr)

            self.cache[key] = rr

            self.fire(write(peer, reply.pack()))

            return

        self.logger.info(
            "Request ({0:s}): {1:s} {2:s} {3:s}".format(
                "{0:s}:{1:d}".format(*peer),
                CLASS.get(qclass), QTYPE.get(qtype), qname
            )
        )

        lookup = DNSRecord(q=DNSQuestion(qname, qtype, qclass))
        id = lookup.header.id
        self.peers[id] = peer
        self.requests[id] = request

        self.fire(write((self.forward, 53), lookup.pack()))

    def response(self, peer, response):
        id = response.header.id
        qname = response.q.qname
        qtype = response.q.qtype
        qclass = response.q.qclass

        if id not in self.peers:
            self.logger.info(
                "Unknown Response ({0:s}): {1:s} {2:s} {3:s}".format(
                    "{0:s}:{1:d}".format(*peer),
                    CLASS.get(qclass), QTYPE.get(qtype), qname
                )
            )

            return

        peer = self.peers[id]
        request = self.requests[id]

        key = (request.q.qname, request.q.qtype, request.q.qclass)

        reply = request.reply()

        reply.add_answer(*response.rr)

        self.cache[key] = reply.rr

        self.fire(write(peer, reply.pack()))

        del self.peers[id]
        del self.requests[id]


def waitfor(host, port, timeout=10):
    sock = socket(AF_INET, SOCK_STREAM)

    while not sock.connect_ex((host, port)) == 0 and timeout:
        timeout -= 1
        sleep(1)

    if timeout <= 0:
        print("Timed out waiting for {0:s}:{1:d}".format(host, port))
        raise SystemExit(1)


def setup_database(args, logger):
    dbhost = args.dbhost
    dbport = args.dbport

    logger.debug(
        "Waiting for Redis Service on {0:s}:{1:d} ...".format(dbhost, dbport)
    )

    waitfor(dbhost, dbport)

    logger.debug(
        "Connecting to Redis on {0:s}:{1:d} ...".format(dbhost, dbport)
    )

    connection_setup(host=dbhost, port=dbport)

    logger.debug("Success!")

    db = get_client()

    return db


def setup_logging(args):
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",

        level=logging.DEBUG if args.debug else logging.INFO,
        stream=args.logfile
    )

    return getLogger(__name__)


def parse_args():
    parser = ArgumentParser(
        formatter_class=ArgumentDefaultsHelpFormatter,
        version=__version__,
    )

    add = parser.add_argument

    add(
        "--debug", action="store_true", default=False,
        dest="debug",
        help="enable debugging mode"
    )

    add(
        "--verbose", action="store_true", default=False,
        dest="verbose",
        help="enable verbose logging"
    )

    add(
        "--logfile", action="store", default="/dev/stdout",
        dest="logfile", metavar="FILE", type=FileType("w"),
        help="write logs to FILE"
    )

    add(
        "--pidfile", action="store", default="udns.pid",
        dest="pidfile", metavar="FILE", type=str,
        help="write process id to FILE"
    )

    add(
        "--dbhost", action="store",
        default=environ.get("REDIS_PORT_6379_TCP_ADDR", "localhost"),
        dest="dbhost", metavar="HOST", type=str,
        help="set database host to HOST (Redis)"
    )

    add(
        "--dbport", action="store",
        default=int(environ.get("REDIS_PORT_6379_TCP_PORT", "6379")),
        dest="dbport", metavar="PORT", type=int,
        help="set database port to PORT (Redis)"
    )

    add(
        "-b", "--bind",
        action="store", type=str,
        default="0.0.0.0:53", dest="bind",
        help="Bind to address:[port]"
    )

    add(
        "-d", "--daemon", action="store_true", default=False,
        dest="daemon",
        help="run as a background process"
    )

    add(
        "-f", "--forward",
        action="store", type=str,
        default="8.8.8.8", dest="forward",
        help="DNS server to forward to"
    )

    return parser.parse_args()


def main():
    args = parse_args()

    logger = setup_logging(args)

    db = setup_database(args, logger)

    Server(args, db, logger).run()


if __name__ == "__main__":
    main()
