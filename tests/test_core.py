"""Test Core"""


from __future__ import print_function

from operator import attrgetter


from dnslib import A, AAAA, CLASS, QTYPE


from .client import query


def test_basic(client, watcher):
    client.fire(query("google-public-dns-a.google.com"))
    assert watcher.wait("reply", "client")
    assert client.a.get_a().rdata == A("8.8.8.8")


def test_hosts(client, watcher):
    client.fire(query("localhost"))
    assert watcher.wait("reply", "client")
    assert (
        set(map(attrgetter("rclass", "rtype", "rdata.data"), client.a.rr)) ==
        set([
            (CLASS.IN, QTYPE.A, A("127.0.0.1").data),
            (CLASS.IN, QTYPE.AAAA, AAAA("::1").data)
        ])
    )
