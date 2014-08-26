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


Managing Zones and Records
--------------------------

udns is a full authoritative, caching dns server and ships with a client to
help manage zones and records. Here are some quick examples:

Create new Zone::
    
    $ udnsc create abc.com.

Create new Zone from a file::
    
    $ udnsc create abc.com. abc.com

or:::
    
    $ udnsc create abc.com. - < abc.com

List Zones::
    
    $ udnsc list

Show Zone Records::
    
    $ udnsc show abc.com.

Export a Zone:::
    
    $ udnsc export abc.com.

.. note:: This exports the Zone to stdout which you can pipe into an output
          file for storage using your shell.
          e.g: ``udnsc export abc.com. > abc.com``

Add Zone Records::
    
    $ udnsc add abc.com. www 127.0.0.1

Delete a Zone Record::
    
    $ udnsc delete abc.com. www

Delete a Zone::
    
    $ udnsc delete abc.com.

.. note:: You __must__ specify zones as fully qualified domain names with a
          trailing period. e.g: ``abc.com.``
