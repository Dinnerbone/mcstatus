from mcstatus.pinger import ServerPinger, AsyncServerPinger
from mcstatus.protocol.connection import (
    TCPSocketConnection,
    UDPSocketConnection,
    TCPAsyncSocketConnection,
    UDPAsyncSocketConnection,
)
from mcstatus.querier import ServerQuerier, AsyncServerQuerier
from mcstatus.bedrock_status import BedrockServerStatus
from mcstatus.scripts.address_tools import parse_address
import dns.resolver


class MinecraftServer:
    """Base class for a Minecraft Java Edition server.

    :param str host: The host/address/ip of the Minecraft server.
    :param int port: The port that the server is on.
    :attr host:
    :attr port:
    """

    def __init__(self, host: str, port: int = 25565):
        self.host = host
        self.port = port

    @staticmethod
    def lookup(address: str):
        """Parses the given address and checks DNS records for an SRV record that points to the Minecraft server.

        :param str address: The address of the Minecraft server, like `example.com:25565`.
        :return: A `MinecraftServer` instance.
        :rtype: MinecraftServer
        """

        host, port = parse_address(address)
        if port is None:
            port = 25565
            try:
                answers = dns.resolver.resolve("_minecraft._tcp." + host, "SRV")
                if len(answers):
                    answer = answers[0]
                    host = str(answer.target).rstrip(".")
                    port = int(answer.port)
            except Exception:
                pass

        return MinecraftServer(host, port)

    def ping(self, tries: int = 3, **kwargs):
        """Checks the latency between a Minecraft Java Edition server and the client (you).

        :param int tries: How many times to retry if it fails.
        :param type **kwargs: Passed to a `ServerPinger` instance.
        :return: The latency between the Minecraft Server and you.
        :rtype: float
        """

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

    async def async_ping(self, tries: int = 3, **kwargs):
        """Asynchronously checks the latency between a Minecraft Java Edition server and the client (you).

        :param int tries: How many times to retry if it fails.
        :param type **kwargs: Passed to a `AsyncServerPinger` instance.
        :return: The latency between the Minecraft Server and you.
        :rtype: float
        """

        connection = TCPAsyncSocketConnection()
        await connection.connect((self.host, self.port))
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

    def status(self, tries: int = 3, **kwargs):
        """Checks the status of a Minecraft Java Edition server via the ping protocol.

        :param int tries: How many times to retry if it fails.
        :param type **kwargs: Passed to a `ServerPinger` instance.
        :return: Status information in a `PingResponse` instance.
        :rtype: PingResponse
        """

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

    async def async_status(self, tries: int = 3, **kwargs):
        """Asynchronously checks the status of a Minecraft Java Edition server via the ping protocol.

        :param int tries: How many times to retry if it fails.
        :param type **kwargs: Passed to a `AsyncServerPinger` instance.
        :return: Status information in a `PingResponse` instance.
        :rtype: PingResponse
        """

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

    def query(self, tries: int = 3):
        """Checks the status of a Minecraft Java Edition server via the query protocol.

        :param int tries: How many times to retry if it fails.
        :return: Query status information in a `QueryResponse` instance.
        :rtype: QueryResponse
        """

        exception = None
        host = self.host
        try:
            answers = dns.resolver.resolve(host, "A")
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

    async def async_query(self, tries: int = 3):
        """Asynchronously checks the status of a Minecraft Java Edition server via the query protocol.

        :param int tries: How many times to retry if it fails.
        :return: Query status information in a `QueryResponse` instance.
        :rtype: QueryResponse
        """

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
                connection = UDPAsyncSocketConnection()
                await connection.connect((host, self.port))
                querier = AsyncServerQuerier(connection)
                await querier.handshake()
                return await querier.read_query()
            except Exception as e:
                exception = e
        else:
            raise exception


class MinecraftBedrockServer:
    """Base class for a Minecraft Bedrock Edition server.

    :param str host: The host/address/ip of the Minecraft server.
    :param int port: The port that the server is on.
    :attr host:
    :attr port:
    """

    def __init__(self, host: str, port: int = 19132):
        self.host = host

        if port is None:
            self.port = 19132
        else:
            self.port = port

    @classmethod
    def lookup(cls, address: str):
        """Parses a given address and returns a MinecraftBedrockServer instance.

        :param str address: The address of the Minecraft server, like `example.com:19132`
        :return: A `MinecraftBedrockServer` instance.
        :rtype: MinecraftBedrockServer
        """

        return cls(*parse_address(address))

    def status(self, tries: int = 3, **kwargs):
        """Checks the status of a Minecraft Bedrock Edition server.

        :param int tries: How many times to retry if it fails.
        :param type **kwargs: Passed to a `BedrockServerStatus` instance.
        :return: Status information in a `BedrockStatusResponse` instance.
        :rtype: BedrockStatusResponse
        """

        exception = None

        for _ in range(tries):
            try:
                resp = BedrockServerStatus(self.host, self.port, **kwargs).read_status()
                break
            except BaseException as e:
                exception = e

        if exception:
            raise exception

        return resp

    async def async_status(self, tries: int = 3, **kwargs):
        """Asynchronously checks the status of a Minecraft Bedrock Edition server.

        :param int tries: How many times to retry if it fails.
        :param type **kwargs: Passed to a `BedrockServerStatus` instance.
        :return: Status information in a `BedrockStatusResponse` instance.
        :rtype: BedrockStatusResponse
        """

        exception = None

        for _ in range(tries):
            try:
                resp = await BedrockServerStatus(self.host, self.port, **kwargs).read_status_async()
                break
            except BaseException as e:
                exception = e

        if exception:
            raise exception

        return resp
