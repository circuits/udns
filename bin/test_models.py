#!/usr/bin/env python


from __future__ import print_function


from dnslib import CLASS, QTYPE  # noqa
from redisco import connection_setup, get_client


from udns.server import Zone, Record  # noqa


connection_setup()
db = get_client()
