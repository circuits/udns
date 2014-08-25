#!/usr/bin/env python


from __future__ import print_function


import sys
import logging
from time import sleep
from os import environ
from logging import getLogger
from socket import AF_INET, SOCK_STREAM, socket
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter


from cachetools import LRUCache

from dnslib import DNSQuestion, DNSRecord
from dnslib import CLASS, QR, QTYPE, RDMAP, RR

from redisco.models import Model
from redisco import connection_setup, get_client
from redisco.models import Attribute, IntegerField, ListField


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

    def add_record(self, rname, rdata, **options):
        rclass = options.get("rclass", CLASS.IN)
        rtype = options.get("rtype", QTYPE.A)
        ttl = options.get("ttl", self.ttl)

        rclass = rclass if rclass is not None else CLASS.IN
        rtype = rtype if rtype is not None else QTYPE.A
        ttl = ttl if ttl is not None else self.ttl

        record = Record(
            rname="{0:s}.{1:s}".format(rname, self.name), rdata=rdata,
            ttl=ttl, rtype=rtype, rclass=rclass
        )
        record.save()
        self.records.append(record)
        self.save()

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
                rr.ttl -= 1
                if rr.ttl <= 0:
                    rrs.remove(rr)
                    if not rrs:
                        del self.cache[k]

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

        lookup = DNSRecord(q=DNSQuestion(qname, qclass, qtype))
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

        for rr in response.rr:
            rr.rname = qname
            reply.add_answer(rr)

        self.cache[key] = reply.rr

        self.fire(write(peer, reply.pack()))

        del self.peers[id]
        del self.requests[id]


def waitfor(address, port, timeout=10):
    sock = socket(AF_INET, SOCK_STREAM)
    while not sock.connect_ex((address, port)) == 0 and timeout:
        sleep(1)


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
    logstream = sys.stderr if args.logfile is None else open(args.logfile, "a")

    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",

        level=logging.DEBUG if args.debug else logging.INFO,
        stream=logstream,
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
        "--daemon", action="store_true", default=False,
        dest="daemon",
        help="run as a background process"
    )

    add(
        "--verbose", action="store_true", default=False,
        dest="verbose",
        help="enable verbose logging"
    )

    add(
        "--logfile", action="store", default=None,
        dest="logfile", metavar="FILE", type=str,
        help="store logging information to FILE"
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
