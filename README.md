udns
====

udns is an authoritative, caching dns server for development and small deployments writtein in [Python][] using the [circuits][] Application Framework and the [dnslib][] DNS library. udns can be run standalone, via [Docker][] or using the [fig][] tool. udns is designed to be small, lightweight, fast and flexible. udns fully supports forwarding, caching as well as honouring ttls.

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

From PyPi (*ccoming soon*):

    $ pip install udns
    $ udnsd  # Server
    $ udnsc  # Client

  [Python]: http://python.org/
  [circuits]: http://circuitsframework.org/
  [dnslib]: https://pypi.python.org/pypi/dnslib
  [Docker]: http://docker.com/
  [fig]: http://fig.sh/