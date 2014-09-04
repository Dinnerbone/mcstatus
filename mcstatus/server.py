import json

from mcstatus.pinger import ServerPinger
from mcstatus.protocol.connection import TCPSocketConnection


class MinecraftServer:
    def __init__(self, host, port=25565):
        self.host = host
        self.port = port

    def ping_server(self, **kwargs):
        connection = TCPSocketConnection((self.host, self.port))
        pinger = ServerPinger(connection, host=self.host, port=self.port, **kwargs)
        pinger.handshake()
        return pinger.read_status(), pinger.test_ping()