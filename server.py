#!/usr/bin/env python


from __future__ import print_function


import sys
import logging
from os import environ
from logging import getLogger
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter


from cachetools import LRUCache
from dnslib import CLASS, QR, QTYPE
from dnslib import DNSQuestion, DNSRecord


from circuits.net.events import write
from circuits.net.sockets import UDPServer
from circuits import Component, Debugger, Event


__version__ = "0.0.1"


class lookup(Event):
    """lookup Event"""


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

    def init(self, args, logger):
        self.args = args
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

    def lookup(self, qname, qclass="IN", qtype="A"):
        request = DNSRecord(
            q=DNSQuestion(
                qname,
                qclass=getattr(CLASS, qclass),
                qtype=getattr(QTYPE, qtype)
            )
        )

        self.fire(write((self.forward, 53), request.pack()))

    def request(self, peer, request):
        qname = request.q.qname
        qtype = QTYPE[request.q.qtype]
        qclass = CLASS[request.q.qclass]

        key = (qname, qtype, qclass)
        if key in self.cache:
            self.logger.info(
                "Cached Request ({0:s}): {1:s} {2:s} {3:s}".format(
                    "{0:s}:{1:d}".format(*peer), qclass, qtype, qname
                )
            )

            reply = self.cache[key]
            reply.header.id = request.header.id
            self.fire(write(peer, reply.pack()))
            return

        self.logger.info(
            "Request ({0:s}): {1:s} {2:s} {3:s}".format(
                "{0:s}:{1:d}".format(*peer), qclass, qtype, qname
            )
        )

        self.peers[key] = peer
        self.requests[key] = request

        self.fire(lookup(qname, qclass=qclass, qtype=qtype))

    def response(self, peer, response):
        qname = response.q.qname
        qtype = QTYPE[response.q.qtype]
        qclass = CLASS[response.q.qclass]

        key = (qname, qtype, qclass)
        if key not in self.peers:
            self.logger.info(
                "Unknown Response ({0:s}): {1:s} {2:s} {3:s}".format(
                    "{0:s}:{1:d}".format(*peer), qclass, qtype, qname
                )
            )

            return

        peer = self.peers[key]
        request = self.requests[key]

        reply = request.reply()

        for rr in response.rr:
            rr.rname = qname
            reply.add_answer(rr)

        reply.pack()
        self.cache[key] = reply

        self.fire(write(peer, reply.pack()))

        del self.peers[key]
        del self.requests[key]


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
        "--pidfile", action="store", default="charla.pid",
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

    Server(args, logger).run()


if __name__ == "__main__":
    main()
