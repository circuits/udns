"""Server"""


from __future__ import print_function


import logging
from time import sleep
from os import environ, path
from logging import getLogger
from collections import defaultdict
from socket import AF_INET, SOCK_STREAM, socket
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter, FileType


from cachetools import LRUCache

from dnslib import DNSQuestion, DNSRecord
from dnslib import A, AAAA, CLASS, QR, QTYPE, RR

from circuits.app import Daemon
from circuits.net.events import write
from circuits.net.sockets import UDPServer
from circuits import Component, Debugger, Event, Timer

from redisco import connection_setup, get_client


from . import __version__
from .models import Record


CNAME = QTYPE.reverse["CNAME"]


class request(Event):
    """request Event"""


class response(Event):
    """response Event"""


class DNS(Component):

    def read(self, peer, data):
        record = DNSRecord.parse(data)
        event = request if record.header.qr == QR.QUERY else response
        return self.fire(event(peer, record))


class Server(Component):

    channel  = "server"

    def init(self, args, db, hosts, logger):
        self.args = args
        self.db = db

        self.hosts = hosts
        self.logger = logger

        self.bind = args.bind
        self.forward = args.forward

        self.peers = {}
        self.requests = {}
        self.cache = LRUCache(maxsize=args.cachesize)

        if args.daemon:
            Daemon(args.pidfile).register(self)

        if args.debug:
            Debugger(events=args.verbose, logger=logger).register(self)

        self.transport = UDPServer(
            self.bind, channel=self.channel
        ).register(self)
        self.protocol = DNS(channel=self.channel).register(self)

    def ready(self, server, bind):
        self.logger.info(
            "DNS Server Ready! Listening on {0:s}:{1:d}".format(*bind)
        )

        # Timer(1, Event.create("ttl"), persist=True, channel=self.channel).register(self)

    def ttl(self):
        for k, rrs in self.cache.items()[:]:
            if any(rr.ttl == 0 for rr in rrs):
                qname, qtype, qclass = k
                self.logger.info(
                    "Expired Entry: {0:s} {1:s} {2:s}".format(
                        CLASS.get(qclass), QTYPE.get(qtype), qname
                    )
                )
                del self.cache[k]
            else:
                for rr in rrs:
                    rr.ttl -= 1

    def request(self, peer, request):
        qname = str(request.q.qname)
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

        if key in self.hosts:
            self.logger.info(
                "Local Hosts Request ({0:s}): {1:s} {2:s} {3:s}".format(
                    "{0:s}:{1:d}".format(*peer),
                    CLASS.get(qclass), QTYPE.get(qtype), qname
                )
            )

            reply = request.reply()
            for rdata in self.hosts[key]:
                rr = RR(
                    qname,
                    rclass=CLASS.IN,
                    rtype=QTYPE.AAAA if ":" in rdata else QTYPE.A,
                    rdata=AAAA(rdata) if ":" in rdata else A(rdata)
                )
                reply.add_answer(rr)

            self.cache[key] = rr

            self.fire(write(peer, reply.pack()))

            return

        records = Record.objects.filter(rname=qname)

        if not records:
            self.logger.info(
                "Request ({0:s}): {1:s} {2:s} {3:s} -> {4:s}:{5:d}".format(
                    "{0:s}:{1:d}".format(*peer),
                    CLASS.get(qclass), QTYPE.get(qtype), qname,
                    self.forward, 53
                )
            )

            lookup = DNSRecord(q=DNSQuestion(qname, qtype, qclass))
            id = lookup.header.id
            self.peers[id] = peer
            self.requests[id] = request

            self.fire(write((self.forward, 53), lookup.pack()))

            return

        self.logger.info(
            "Authoritative Request ({0:s}): {1:s} {2:s} {3:s}".format(
                "{0:s}:{1:d}".format(*peer),
                CLASS.get(qclass), QTYPE.get(qtype), qname
            )
        )

        rr = []
        reply = request.reply()

        if len(records) == 1 and records[0].rtype == CNAME:
            rr.append(records[0].rr)
            records = Record.objects.filter(rname=records[0].rdata)

        for record in records:
            rr.append(record.rr)

        reply.add_answer(*rr)

        self.cache[key] = rr

        self.fire(write(peer, reply.pack()))

    def response(self, peer, response):
        id = response.header.id

        qname = str(response.q.qname)
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

        key = (str(request.q.qname), request.q.qtype, request.q.qclass)

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


def parse_args(args=None):
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
        "--cachesize", action="store",
        default=int(environ.get("CACHESIZEE", "1024")),
        dest="cachesize", metavar="SIZEe", type=int,
        help="set cache size to SIZE"
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

    return parser.parse_args(args)


def parse_hosts(filename):
    hosts = defaultdict(list)

    if path.exists(filename):
        with open(filename, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                tokens = line.split()
                rdata, labels = tokens[0], tokens[1:]
                for label in labels:
                    if not label.endswith("."):
                        label = "{0:s}.".format(label)
                    key = (label, QTYPE.A, CLASS.IN)
                    hosts[key].append(rdata)

    return hosts


def main():
    args = parse_args()

    logger = setup_logging(args)

    db = setup_database(args, logger)

    hosts = parse_hosts("/etc/hosts")

    Server(args, db, hosts, logger).run()


if __name__ == "__main__":
    main()
