from mcstatus.pinger import ServerPinger, AsyncServerPinger
from mcstatus.protocol.connection import TCPSocketConnection, UDPSocketConnection, TCPAsyncSocketConnection
from mcstatus.querier import ServerQuerier
from mcstatus.scripts.address_tools import parse_address
import dns.resolver


class MinecraftServer:
    def __init__(self, host, port=25565):
        self.host = host
        self.port = port

    @staticmethod
    def lookup(address):
        host, port = parse_address(address)
        if port is None:
            port = 25565
            try:
                answers = dns.resolver.query("_minecraft._tcp." + host, "SRV")
                if len(answers):
                    answer = answers[0]
                    host = str(answer.target).rstrip(".")
                    port = int(answer.port)
            except Exception:
                pass

        return MinecraftServer(host, port)

    def ping(self, tries=3, **kwargs):
        connection = TCPSocketConnection((self.host, self.port))
        exception = None
        for attempt in range(tries):
            try:
                pinger = ServerPinger(connection, host=self.host, port=self.port, **kwargs)
                pinger.handshake()
                return pinger.test_ping()
            except Exception as e:
                exception = e
        else:
            raise exception

    async def async_ping(self, tries=3, **kwargs):
        connection = await TCPAsyncSocketConnection((self.host, self.port))
        exception = None
        for attempt in range(tries):
            try:
                pinger = AsyncServerPinger(connection, host=self.host, port=self.port, **kwargs)
                pinger.handshake()
                return await pinger.test_ping()
            except Exception as e:
                exception = e
        else:
            raise exception

    def status(self, tries=3, **kwargs):
        connection = TCPSocketConnection((self.host, self.port))
        exception = None
        for attempt in range(tries):
            try:
                pinger = ServerPinger(connection, host=self.host, port=self.port, **kwargs)
                pinger.handshake()
                result = pinger.read_status()
                result.latency = pinger.test_ping()
                return result
            except Exception as e:
                exception = e
        else:
            raise exception

    async def async_status(self, tries=3, **kwargs):
        connection = TCPAsyncSocketConnection()
        await connection.connect((self.host, self.port))
        exception = None
        for attempt in range(tries):
            try:
                pinger = AsyncServerPinger(connection, host=self.host, port=self.port, **kwargs)
                pinger.handshake()
                result = await pinger.read_status()
                result.latency = await pinger.test_ping()
                return result
            except Exception as e:
                exception = e
        else:
            raise exception

    def query(self, tries=3):
        exception = None
        host = self.host
        try:
            answers = dns.resolver.query(host, "A")
            if len(answers):
                answer = answers[0]
                host = str(answer).rstrip(".")
        except Exception as e:
            pass
        for attempt in range(tries):
            try:
                connection = UDPSocketConnection((host, self.port))
                querier = ServerQuerier(connection)
                querier.handshake()
                return querier.read_query()
            except Exception as e:
                exception = e
        else:
            raise exception

    async def async_query(self, tries=3):
        raise NotImplementedError # TODO: '-'