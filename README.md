udns
====

udns is an authoritative, caching DNS server for development and small deployments written in [Python][] using the [circuits][] Application Framework and the [dnslib][] DNS library. udns can be run standalone, via [Docker][] or using the [fig][] tool. udns is designed to be small, lightweight, fast and flexible. udns fully supports forwarding, caching as well as honoring TTL(s).

Installation and Usage
----------------------

From Source:

    $ hg clone https://bitbucket.org/circuits/udns
    $ cd udns
    $ python setup.py develop
    $ sudo udnsd --debug  # Server
    $ udnsc --help        # Client

From Source using [fig][] and [Docker][]:

    $ hg clone https://bitbucket.org/circuits/udns
    $ cd udns
    $ fig up                   # Server
    $ fig run --rm udns udnsc  # Client

Using [Docker][]:

    $ docker run -d -p 53:53/udp prologic/udns

From PyPi (*coming soon*):

    $ pip install udns
    $ udnsd  # Server
    $ udnsc  # Client

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
  [Python]: http://python.org/
  [circuits]: http://circuitsframework.org/
  [dnslib]: https://pypi.python.org/pypi/dnslib
  [Docker]: http://docker.com/
  [fig]: http://fig.sh/