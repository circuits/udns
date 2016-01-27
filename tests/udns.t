start udnsd:

  $ udnsd --bind 127.0.0.1:53000 --dbhost redis --daemon --pidfile /tmp/udnsd.pid

  $ sleep 1

stop udnsd:

  $ kill $(cat /tmp/udnsd.pid)
