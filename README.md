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
