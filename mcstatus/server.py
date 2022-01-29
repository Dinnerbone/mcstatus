import re

from mcstatus.pinger import PingResponse, ServerPinger, AsyncServerPinger
from mcstatus.protocol.connection import (
    TCPSocketConnection,
    UDPSocketConnection,
    TCPAsyncSocketConnection,
    UDPAsyncSocketConnection,
)
from mcstatus.querier import QueryResponse, ServerQuerier, AsyncServerQuerier
from mcstatus.bedrock_status import BedrockServerStatus, BedrockStatusResponse
from mcstatus.scripts.address_tools import parse_address
from mcstatus.utils import retry
import dns.resolver
from dns.exception import DNSException

VALID_HOSTNAME_REGEX = re.compile(
    r"(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-]*[A-Za-z0-9])"
)

__all__ = ["MinecraftServer", "MinecraftBedrockServer"]


def ensure_valid_ip(host: object, port: object):
    if not isinstance(host, str):
        raise TypeError(f"Host must be a string address, got {type(host)} ({host!r})")
    if not isinstance(port, int):
        raise TypeError(f"Port must be an integer port number, got {type(port)} ({port})")
    if port > 65535 or port < 0:
        raise ValueError(f"Port must be within the allowed range (0-2^16), got {port}")
    if not VALID_HOSTNAME_REGEX.fullmatch(host):
        raise ValueError(f"Invalid host address, {host!r} (doesn't match the required pattern)")


class MinecraftServer:
    """Base class for a Minecraft Java Edition server.

    :param str host: The host/address/ip of the Minecraft server.
    :param int port: The port that the server is on.
    :param float timeout: The timeout in seconds before failing to connect.
    :attr host:
    :attr port:
    """

    def __init__(self, host: str, port: int = 25565, timeout: float = 3):
        ensure_valid_ip(host, port)
        self.host = host
        self.port = port
        self.timeout = timeout

    @classmethod
    def lookup(cls, address: str, timeout: float = 3):
        """Parses the given address and checks DNS records for an SRV record that points to the Minecraft server.

        :param str address: The address of the Minecraft server, like `example.com:25565`.
        :param float timeout: The timeout in seconds before failing to connect.
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

        return cls(host, port, timeout)

    def ping(self, **kwargs) -> float:
        """Checks the latency between a Minecraft Java Edition server and the client (you).

        :param type **kwargs: Passed to a `ServerPinger` instance.
        :return: The latency between the Minecraft Server and you.
        :rtype: float
        """

        connection = TCPSocketConnection((self.host, self.port), self.timeout)
        return self._retry_ping(connection, **kwargs)

    @retry(tries=3)
    def _retry_ping(self, connection: TCPSocketConnection, **kwargs) -> float:
        pinger = ServerPinger(connection, host=self.host, port=self.port, **kwargs)
        pinger.handshake()
        return pinger.test_ping()

    async def async_ping(self, **kwargs) -> float:
        """Asynchronously checks the latency between a Minecraft Java Edition server and the client (you).

        :param type **kwargs: Passed to a `AsyncServerPinger` instance.
        :return: The latency between the Minecraft Server and you.
        :rtype: float
        """

        connection = TCPAsyncSocketConnection()
        await connection.connect((self.host, self.port), self.timeout)
        return await self._retry_async_ping(connection, **kwargs)

    @retry(tries=3)
    async def _retry_async_ping(self, connection: TCPAsyncSocketConnection, **kwargs) -> float:
        pinger = AsyncServerPinger(connection, host=self.host, port=self.port, **kwargs)
        pinger.handshake()
        ping = await pinger.test_ping()
        return ping

    def status(self, **kwargs) -> PingResponse:
        """Checks the status of a Minecraft Java Edition server via the ping protocol.

        :param type **kwargs: Passed to a `ServerPinger` instance.
        :return: Status information in a `PingResponse` instance.
        :rtype: PingResponse
        """

        connection = TCPSocketConnection((self.host, self.port), self.timeout)
        return self._retry_status(connection, **kwargs)

    @retry(tries=3)
    def _retry_status(self, connection: TCPSocketConnection, **kwargs) -> PingResponse:
        pinger = ServerPinger(connection, host=self.host, port=self.port, **kwargs)
        pinger.handshake()
        result = pinger.read_status()
        result.latency = pinger.test_ping()
        return result

    async def async_status(self, **kwargs) -> PingResponse:
        """Asynchronously checks the status of a Minecraft Java Edition server via the ping protocol.

        :param type **kwargs: Passed to a `AsyncServerPinger` instance.
        :return: Status information in a `PingResponse` instance.
        :rtype: PingResponse
        """

        connection = TCPAsyncSocketConnection()
        await connection.connect((self.host, self.port), self.timeout)
        return await self._retry_async_status(connection, **kwargs)

    @retry(tries=3)
    async def _retry_async_status(self, connection: TCPAsyncSocketConnection, **kwargs) -> PingResponse:
        pinger = AsyncServerPinger(connection, host=self.host, port=self.port, **kwargs)
        pinger.handshake()
        result = await pinger.read_status()
        result.latency = await pinger.test_ping()
        return result

    def query(self) -> QueryResponse:
        """Checks the status of a Minecraft Java Edition server via the query protocol.

        :return: Query status information in a `QueryResponse` instance.
        :rtype: QueryResponse
        """
        host = self.host
        try:
            answers = dns.resolver.resolve(host, "A")
            if len(answers):
                answer = answers[0]
                host = str(answer).rstrip(".")
        except DNSException:
            pass

        return self._retry_query(host)

    @retry(tries=3)
    def _retry_query(self, host: str) -> QueryResponse:
        connection = UDPSocketConnection((host, self.port), self.timeout)
        querier = ServerQuerier(connection)
        querier.handshake()
        return querier.read_query()

    async def async_query(self) -> QueryResponse:
        """Asynchronously checks the status of a Minecraft Java Edition server via the query protocol.

        :return: Query status information in a `QueryResponse` instance.
        :rtype: QueryResponse
        """
        host = self.host
        try:
            answers = dns.resolver.resolve(host, "A")
            if len(answers):
                answer = answers[0]
                host = str(answer).rstrip(".")
        except DNSException:
            pass

        return await self._retry_async_query(host)

    @retry(tries=3)
    async def _retry_async_query(self, host) -> QueryResponse:
        connection = UDPAsyncSocketConnection()
        await connection.connect((host, self.port), self.timeout)
        querier = AsyncServerQuerier(connection)
        await querier.handshake()
        return await querier.read_query()


class MinecraftBedrockServer:
    """Base class for a Minecraft Bedrock Edition server.

    :param str host: The host/address/ip of the Minecraft server.
    :param int port: The port that the server is on.
    :param float timeout: The timeout in seconds before failing to connect.
    :attr host:
    :attr port:
    """

    def __init__(self, host: str, port: int = 19132, timeout: float = 3):
        ensure_valid_ip(host, port)
        self.host = host
        self.port = port
        self.timeout = timeout

    @classmethod
    def lookup(cls, address: str):
        """Parses a given address and returns a MinecraftBedrockServer instance.

        :param str address: The address of the Minecraft server, like `example.com:19132`
        :return: A `MinecraftBedrockServer` instance.
        :rtype: MinecraftBedrockServer
        """
        host, port = parse_address(address)
        # If the address didn't contain port, fall back to constructor's default
        if port is None:
            return cls(host)
        return cls(host, port)

    @retry(tries=3)
    def status(self, **kwargs) -> BedrockStatusResponse:
        """Checks the status of a Minecraft Bedrock Edition server.

        :param type **kwargs: Passed to a `BedrockServerStatus` instance.
        :return: Status information in a `BedrockStatusResponse` instance.
        :rtype: BedrockStatusResponse
        """
        return BedrockServerStatus(self.host, self.port, self.timeout, **kwargs).read_status()

    @retry(tries=3)
    async def async_status(self, **kwargs) -> BedrockStatusResponse:
        """Asynchronously checks the status of a Minecraft Bedrock Edition server.

        :param type **kwargs: Passed to a `BedrockServerStatus` instance.
        :return: Status information in a `BedrockStatusResponse` instance.
        :rtype: BedrockStatusResponse
        """
        return await BedrockServerStatus(self.host, self.port, self.timeout, **kwargs).read_status_async()
