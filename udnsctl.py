#!/usr/bin/env python


from __future__ import print_function


from os import environ
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter


from dnslib import CLASS, QTYPE

from redisco import connection_setup


from server import Zone


__version__ = "0.0.1"


def add(args):
    zones = Zone.objects.filter(name=args.zone)

    if zones:
        zone = zones[0]
    else:
        zone = Zone(name=args.zone)
        zone.save()

    if args.rname and args.rdata:
        zone.add_record(
            args.rname, args.rdata,
            rclass=getattr(CLASS, args.rclass),
            rtype=getattr(QTYPE, args.rtype)
        )


def delete(args):
    zones = Zone.objects.filter(name=args.zone)

    if not zones:
        print("Zone {0:s} not found!".format(args.zone))
        raise SystemExit(1)

    zone = zones[0]

    if args.rname:
        zone.delete_record(args.rname)
    else:
        zone.delete()


def list(args):
    print("\n".join(zone.name for zone in Zone.objects.all()))


def show(args):
    zones = Zone.objects.filter(name=args.zone)

    if not zones:
        print("Zone {0:s} not found!".format(args.zone))
        raise SystemExit(1)

    zone = zones[0]

    print("\n".join(record.rr.toZone() for record in zone.records))


def setup_database(args):
    dbhost = args.dbhost
    dbport = args.dbport

    connection_setup(host=dbhost, port=dbport)


def parse_args():
    parser = ArgumentParser(
        formatter_class=ArgumentDefaultsHelpFormatter,
        version=__version__,
    )

    parser.add_argument(
        "--dbhost", action="store",
        default=environ.get("REDIS_PORT_6379_TCP_ADDR", "localhost"),
        dest="dbhost", metavar="HOST", type=str,
        help="set database host to HOST (Redis)"
    )

    parser.add_argument(
        "--dbport", action="store",
        default=int(environ.get("REDIS_PORT_6379_TCP_PORT", "6379")),
        dest="dbport", metavar="PORT", type=int,
        help="set database port to PORT (Redis)"
    )

    # Commands

    subparsers = parser.add_subparsers(
        title="Commands",
        description="Available Commands",
        help="Description"
    )

    # add
    add_parser = subparsers.add_parser(
        "add",
        help="Add a Zone or Record entry"
    )
    add_parser.set_defaults(func=add)

    add_parser.add_argument(
        "-c", "--class", default="IN", metavar="RCLASS", type=str,
        dest="rclass", choices=CLASS.forward.keys(),
        help="Resource class to add"
    )

    add_parser.add_argument(
        "-t", "--type", default="A", metavar="RTYPE", type=str,
        dest="rtype", choices=QTYPE.forward.keys(),
        help="Resource type to add"
    )

    add_parser.add_argument(
        "zone", metavar="ZONE", type=str,
        help="Zone to add"
    )

    add_parser.add_argument(
        "rname", nargs="?", default=None, metavar="RNAME", type=str,
        help="Resource name to add"
    )

    add_parser.add_argument(
        "rdata", nargs="?", default=None, metavar="RDATA", type=str,
        help="Resoufce data to add"
    )

    # delete
    delete_parser = subparsers.add_parser(
        "delete",
        help="Delete a Zone or Record"
    )
    delete_parser.set_defaults(func=delete)

    delete_parser.add_argument(
        "zone", metavar="ZONE", type=str,
        help="Zone to delete"
    )

    delete_parser.add_argument(
        "rname", nargs="?", default=None, metavar="RNAME", type=str,
        help="Resource name to delete"
    )

    # list
    list_parser = subparsers.add_parser(
        "list",
        help="List Zones"
    )
    list_parser.set_defaults(func=list)

    # show
    show_parser = subparsers.add_parser(
        "show",
        help="Display records of a zone"
    )
    show_parser.set_defaults(func=show)

    show_parser.add_argument(
        "zone", metavar="ZONE", type=str,
        help="Zone to display"
    )

    return parser.parse_args()


def main():
    args = parse_args()
    setup_database(args)
    args.func(args)


if __name__ == "__main__":
    main()
