#!/usr/bin/env python


from redisco import connection_setup, get_client


connection_setup()
db = get_client()
db.flushall()
