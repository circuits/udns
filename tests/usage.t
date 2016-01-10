udnsd Usage:

  $ udnsd --help
  usage: udnsd [-h] [-v] [--debug] [--verbose] [--logfile FILE] [--pidfile FILE]
               [--dbhost HOST] [--dbport PORT] [--cachesize SIZEe] [-b BIND]
               [-d] [-f FORWARD]
  
  optional arguments:
    -h, --help            show this help message and exit
    -v, --version         show program's version number and exit
    --debug               enable debugging mode (default: False)
    --verbose             enable verbose logging (default: False)
    --logfile FILE        write logs to FILE (default: /dev/stdout)
    --pidfile FILE        write process id to FILE (default: udns.pid)
    --dbhost HOST         set database host to HOST (Redis) (default: localhost)
    --dbport PORT         set database port to PORT (Redis) (default: 6379)
    --cachesize SIZEe     set cache size to SIZE (default: 1024)
    -b BIND, --bind BIND  Bind to address:[port] (default: 0.0.0.0:53)
    -d, --daemon          run as a background process (default: False)
    -f FORWARD, --forward FORWARD
                          DNS server to forward to (default: 8.8.8.8)

udnsc Usage:

  $ udnsc --help
  usage: udnsc [-h] [-v] [--dbhost HOST] [--dbport PORT]
               {create,add,delete,list,show,export,dbshell} ...
  
  optional arguments:
    -h, --help            show this help message and exit
    -v, --version         show program's version number and exit
    --dbhost HOST         set database host to HOST (Redis) (default: localhost)
    --dbport PORT         set database port to PORT (Redis) (default: 6379)
  
  Commands:
    Available Commands
  
    {create,add,delete,list,show,export,dbshell}
                          Description
      create              Create a new Zone
      add                 Add a Zone or Record entry
      delete              Delete a Zone or Record
      list                List Zones
      show                Display records of a zone
      export              Export a Zone
      dbshell             Interactive DB Shell
