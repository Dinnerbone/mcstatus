mcstatus
========

`mcstatus` provides an easy way to query Minecraft servers for any information they can expose.
It provides two modes of access, `query` and `ping`, the differences of which are listed below in usage.

Usage
-----

```python
from mcstatus import MinecraftServer

server = MinecraftServer("localhost", 25565)

# 'ping' is supported by all Minecraft servers that are version 1.7 or higher.
status = server.ping_server()
print("The server has %d players" % (status.players.online))

# 'query' has to be enabled in a servers' server.properties file.
# It may give more information than a ping, such as a full player list or mod information.
query = query.query_server()
print("The server has the following players online: " % (string.join(query.players.names, ", ")))
```

Installation
------------

mcstatus is available on pypi, and can be installed trivially with:

```bash
pip install mcstatus
```

Alternatively, just clone this repo!

License
-------

mcstatus is licensed under Apache 2.0.
