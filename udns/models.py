# Module:   models
# Date:     30th August 2014
# Author:   James Mills, prologic at shortcircuit dot net dot au


"""Data Models"""


from dnslib import ZoneParser
from dnslib import CLASS, QTYPE, RDMAP, RR

from redisco.models import Model
from redisco.models import Attribute, IntegerField, ListField


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
            self.name
            if rname == "@"
            else "{0:s}.{1:s}".format(rname, self.name),
            rdata,
            rclass=rclass, rtype=rtype, ttl=ttl
        )

    def delete_record(self, rname):
        fullname = (
            self.name
            if rname == "@"
            else
            "{0:s}.{1:s}".format(rname, self.name)
        )

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

    def load(self, f):
        parser = ZoneParser(f.read())

        for rr in list(parser):
            rname = str(rr.rname)
            rdata = str(rr.rdata)
            rclass = rr.rclass
            rtype = rr.rtype
            ttl = rr.ttl

            self._add_record(rname, rdata, rclass=rclass, rtype=rtype, ttl=ttl)

        self.ttl = parser.ttl
        self.save()

    def export(self):
        out = [
            "$TTL {0:d}".format(self.ttl),
            "$ORIGIN {0:s}".format(self.name.rstrip(".")),
            "",
        ]

        for record in self.records:
            rr = record.rr
            rname = str(rr.rname.stripSuffix(self.name))
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
