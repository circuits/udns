.. _dnslib: https://pypi.python.org/pypi/dnslib
.. _circuits: http://circuitsframework.org/
.. _Docker: http://docker.com/
.. _Python: http://python.org/
.. _fig: http://fig.sh/


udns
====

charla is `Spanish for chat <http://www.spanishcentral.com/translate/charla>`_
and is an IRC Server and Daemon written in `Python`_ using the `circuits`_
Application Framework.


Installation and Usage
----------------------

From Source::
    
    $ hg clone https://bitbucket.org/circuits/charla
    $ cd charla
    $ ./server.py

From Source using `fig`_ and `Docker`_::
    
    $ hg clone https://bitbucket.org/circuits/charla
    $ cd charla
    $ fig up

Using `Docker`_::
    
    $ docker run -d 6667:6667 prologic/charla

From PyPi (*ccoming soon*)::
    
    $ pip install charla
    $ charla
