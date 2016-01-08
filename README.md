udns
====

[!['Stories in Ready'](https://badge.waffle.io/prologic/udns.png?label=ready&title=Ready)](https://waffle.io/prologic/udns)

udns is an authoritative, caching DNS server for development and small deployments written in [Python](http://python.org/) using the [circuits](http://circuitsframework.org/) Application Framework and the [dnslib](https://pypi.python.org/pypi/dnslib) DNS library. udns can be run standalone, via [Docker](http://docker.com/) or using the [Docker Compose](https://docs.docker.com/compose/) tool. udns is designed to be small, lightweight, fast and flexible. udns fully supports forwarding, caching as well as honoring TTL(s). udns will also read your `/etc/hosts` file at startup and use this to populate an internal hosts cache so that entries in your local `/etc/hosts` file are fully resolvable with tools such as `host`, `dig` and resolver client libraries.

Installation and Usage
----------------------

From Source:

    $ git clone https://github.com/prologic/udns
    $ cd udns
    $ python setup.py develop
    $ sudo udnsd --debug  # Server
    $ udnsc --help        # Client

From Source using [Docker](http://docker.com/) and [Docker Compose](https://docs.docker.com/compose/):

    $ git clone https://github.com/prologic/udns
    $ cd udns
    $ docker-compose up -d                  # Server
    $ docker-compose run --rm udns udnsc    # Client

Using [Docker](http://docker.com/):

    $ docker run -d -p 53:53/udp prologic/udns

From PyPi (*coming soon*):

    $ pip install udns
    $ udnsd     # Server
    $ udnsc     # Client

Running as a Daemon:

    $ sudo udnsd -d --logfile=$(pwd)/udnsd.log --pidfile=$(pwd)/udnsd.pid

Managing Zones and Records
--------------------------

udns is a full authoritative, caching DNS server and ships with a client to help manage zones and records. Here are some quick examples:

Create new Zone:

    $ udnsc create abc.com.

Create new Zone from a file:

    $ udnsc create abc.com. abc.com

or::

    $ udnsc create abc.com. - < abc.com

List Zones:

    $ udnsc list

Show Zone Records:

    $ udnsc show abc.com.

Export a Zone::

    $ udnsc export abc.com.

> **note**
>
> This exports the Zone to stdout which you can pipe into an output  
> file for storage using your shell. e.g: `udnsc export abc.com. > abc.com`
>
Add Zone Records:

    $ udnsc add abc.com. www 127.0.0.1

Delete a Zone Record:

    $ udnsc delete abc.com. www

Delete a Zone:

    $ udnsc delete abc.com.

> **note**
>
> You \_\_must\_\_ specify zones as fully qualified domain names with a  
> trailing period. e.g: `abc.com.`
>

