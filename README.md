![travis build status](	https://img.shields.io/travis/Dinnerbone/mcstatus/master.svg)
![current version](https://img.shields.io/pypi/v/mcstatus.svg)
![supported python versions](https://img.shields.io/pypi/pyversions/mcstatus.svg)

mcstatus
========

`mcstatus` provides an easy way to query Minecraft servers for any information they can expose.
It provides three modes of access (`query`, `status` and `ping`), the differences of which are listed below in usage.

Usage
-----

```python
from mcstatus import MinecraftServer

# If you know the host and port, you may skip this and use MinecraftServer("example.org", 1234)
server = MinecraftServer.lookup("example.org:1234")

# 'status' is supported by all Minecraft servers that are version 1.7 or higher.
status = server.status()
print("The server has {0} players and replied in {1} ms".format(status.players.online, status.latency))

# 'ping' is supported by all Minecraft servers that are version 1.7 or higher.
# It is included in a 'status' call, but is exposed separate if you do not require the additional info.
latency = server.ping()
print("The server replied in {0} ms".format(latency))

# 'query' has to be enabled in a servers' server.properties file.
# It may give more information than a ping, such as a full player list or mod information.
query = server.query()
print("The server has the following players online: {0}".format(", ".join(query.players.names)))
```

Command Line Interface
```
$ mcstatus
Usage: mcstatus [OPTIONS] ADDRESS COMMAND [ARGS]...

  mcstatus provides an easy way to query Minecraft servers for any
  information they can expose. It provides three modes of access: query,
  status, and ping.

  Examples:

  $ mcstatus example.org ping
  21.120ms

  $ mcstatus example.org:1234 ping
  159.903ms

  $ mcstatus example.org status
  version: v1.8.8 (protocol 47)
  description: "A Minecraft Server"
  players: 1/20 ['Dinnerbone (61699b2e-d327-4a01-9f1e-0ea8c3f06bc6)']

  $ mcstatus example.org query
  host: 93.148.216.34:25565
  software: v1.8.8 vanilla
  plugins: []
  motd: "A Minecraft Server"
  players: 1/20 ['Dinnerbone (61699b2e-d327-4a01-9f1e-0ea8c3f06bc6)']

Options:
  -h, --help  Show this message and exit.

Commands:
  json    combination of several other commands with json formatting
  ping    prints server latency
  query   detailed server information
  status  basic server information
```

Installation
------------

mcstatus is available on pypi, and can be installed trivially with:

```bash
python3 -m pip install mcstatus
```

Alternatively, just clone this repo!

License
-------

mcstatus is licensed under Apache 2.0.
