"""Test Client"""


from dnslib import DNSQuestion, DNSRecord, CLASS, QTYPE

from circuits import Event, Component
from circuits.net.events import write
from circuits.net.sockets import UDPClient


class query(Event):
    """query Event"""


class reply(Event):
    """reply Event"""


class DNS(Component):
    """DNS Protocol Handling"""

    def read(self, peer, data):
        self.fire(reply(DNSRecord.parse(data)))


class Client(Component):

    channel = "client"

    def init(self, server, port):
        self.server = server
        self.port = int(port)

        self.transport = UDPClient(
            ("127.0.0.1", 0), channel=self.channel
        ).register(self)
        self.protocol = DNS(channel=self.channel).register(self)

    def reply(self, a):
        self.a = a

    def query(self, qname, qtype="A", qclass="IN"):
        qtype = QTYPE.reverse[qtype]
        qclass = CLASS.reverse[qclass]

        q = DNSRecord(q=DNSQuestion(qname, qtype, qclass))

        self.fire(write((self.server, self.port), q.pack()))
