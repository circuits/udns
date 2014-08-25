#!/usr/bin/env python


from __future__ import print_function


from dnslib import CLASS, QTYPE
from redisco import connection_setup, get_client


from server import Zone, Record  # noqa


connection_setup()
db = get_client()
db.flushall()

abc = Zone(name="abc.com")
abc.save()

r = Record(rname="www.abc.com.", rdata="1.2.3.4")
r.save()

abc.records.append(r)
abc.save()
