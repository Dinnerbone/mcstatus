from mcstatus.pinger import ServerPinger
from mcstatus.protocol.connection import TCPSocketConnection, UDPSocketConnection
from mcstatus.querier import ServerQuerier


class MinecraftServer:
    def __init__(self, host, port=25565):
        self.host = host
        self.port = port

    def ping_server(self, retries=3, **kwargs):
        attempt = 0
        connection = TCPSocketConnection((self.host, self.port))
        exception = None
        while attempt < retries:
            try:
                pinger = ServerPinger(connection, host=self.host, port=self.port, **kwargs)
                pinger.handshake()
                return pinger.read_status(), pinger.test_ping()
            except Exception as e:
                exception = e
                attempt += 1
        raise exception

    def query_server(self, retries=3):
        attempt = 0
        exception = None
        while attempt < retries:
            try:
                connection = UDPSocketConnection((self.host, self.port))
                querier = ServerQuerier(connection)
                querier.handshake()
                return querier.read_query()
            except Exception as e:
                exception = e
                attempt += 1
        raise exception