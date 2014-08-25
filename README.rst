.. _dnslib: https://pypi.python.org/pypi/dnslib
.. _circuits: http://circuitsframework.org/
.. _Docker: http://docker.com/
.. _Python: http://python.org/
.. _fig: http://fig.sh/


udns
====

udns is an authoritative, caching dns server for development and small
deployments writtein in `Python`_ using the `circuits`_ Application Framework
and the `dnslib`_ DNS library. udns can be run standalone, via `Docker`_
or using the `fig`_ tool. udns is designed to be small, lightweight, fast
and flexible. udns fully supports forwarding, caching as well as honouring
ttls.


Installation and Usage
----------------------

From Source::
    
    $ hg clone https://bitbucket.org/circuits/udns
    $ cd udns
    $ python setup.py develop
    $ sudo udnsd --debug  # Server
    $ udnsc --help        # Client

From Source using `fig`_ and `Docker`_::
    
    $ hg clone https://bitbucket.org/circuits/udns
    $ cd udns
    $ fig up                   # Server
    $ fig run --rm udns udnsc  # Client

Using `Docker`_::
    
    $ docker run -d -p 53:53/udp prologic/udns

From PyPi (*ccoming soon*)::
    
    $ pip install udns
    $ udnsd  # Server
    $ udnsc  # Client
