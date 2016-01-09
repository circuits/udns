# Module:   client
# Date:     30th August 2014
# Author:   James Mills, prologic at shortcircuit dot net dot au


"""Client"""


from __future__ import print_function


from os import environ
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter, FileType
from code import InteractiveConsole


from dnslib import CLASS, QTYPE

from redisco import connection_setup


from .models import Zone
from . import __version__


def create(args):
    zone = Zone.objects.filter(name=args.zone).first()

    if zone:
        print("Zone {0:s} already exists!".format(args.zone))
        raise SystemExit(1)

    zone = Zone(name=args.zone, ttl=args.ttl)
    zone.save()

    if args.file is not None:
        zone.load(args.file)


def add(args):
    zone = Zone.objects.filter(name=args.zone).first()

    if not zone:
        print("Zone {0:s} not found!".format(args.zone))
        raise SystemExit(1)

    if args.rname and args.rdata:
        zone.add_record(
            args.rname, args.rdata, ttl=args.ttl,
            rclass=getattr(CLASS, args.rclass),
            rtype=getattr(QTYPE, args.rtype)
        )
    else:
        print("Must specify both a name and data!")
        raise SystemExit(1)


def delete(args):
    zone = Zone.objects.filter(name=args.zone).first()

    if not zone:
        print("Zone {0:s} not found!".format(args.zone))
        raise SystemExit(1)

    if args.rname:
        zone.delete_record(args.rname)
    else:
        zone.delete()


def list(args):
    print("\n".join(zone.name for zone in Zone.objects.all()))


def show(args):
    zone = Zone.objects.filter(name=args.zone).first()

    if not zone:
        print("Zone {0:s} not found!".format(args.zone))
        raise SystemExit(1)

    print("\n".join(record.rr.toZone() for record in zone.records))


def export(args):
    zone = Zone.objects.filter(name=args.zone).first()

    if not zone:
        print("Zone {0:s} not found!".format(args.zone))
        raise SystemExit(1)

    print(zone.export())


def dbshell(args):
    vars = {}
    vars.update(globals())
    vars.update(locals())
    console = InteractiveConsole(vars)
    console.interact()


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

    # create
    create_parser = subparsers.add_parser(
        "create",
        help="Create a new Zone"
    )
    create_parser.set_defaults(func=create)

    create_parser.add_argument(
        "--ttl", default=None, metavar="TTL", type=int,
        help="Zone default ttl"
    )

    create_parser.add_argument(
        "zone", metavar="ZONE", type=str,
        help="Name of zone to create"
    )

    create_parser.add_argument(
        "file", metavar="FILE", default=None, nargs="?", type=FileType("r"),
        help="Zone file to import"
    )

    # add
    add_parser = subparsers.add_parser(
        "add",
        help="Add a Zone or Record entry"
    )
    add_parser.set_defaults(func=add)

    add_parser.add_argument(
        "--class", default="IN", metavar="RCLASS", type=str,
        dest="rclass", choices=CLASS.reverse.keys(),
        help="Resource class to add"
    )

    add_parser.add_argument(
        "--type", default="A", metavar="RTYPE", type=str,
        dest="rtype", choices=QTYPE.reverse.keys(),
        help="Resource type to add"
    )

    add_parser.add_argument(
        "--ttl", default=None, metavar="TTL", type=int,
        help="Resource ttl to add"
    )

    add_parser.add_argument(
        "zone", metavar="ZONE", type=str,
        help="Zone to add resource to"
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

    # export
    export_parser = subparsers.add_parser(
        "export",
        help="Export a Zone"
    )
    export_parser.set_defaults(func=export)

    export_parser.add_argument(
        "zone", metavar="ZONE", type=str,
        help="Zone to export"
    )

    # dbshell
    dbshell_parser = subparsers.add_parser(
        "dbshell",
        help="Interactive DB Shell"
    )
    dbshell_parser.set_defaults(func=dbshell)

    return parser.parse_args()


def main():
    args = parse_args()
    setup_database(args)
    args.func(args)


if __name__ == "__main__":
    main()
