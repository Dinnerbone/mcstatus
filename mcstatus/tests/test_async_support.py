from inspect import iscoroutinefunction

from mcstatus.protocol.connection import (
    TCPAsyncSocketConnection,
    UDPAsyncSocketConnection,
)


def test_is_completely_asynchronous():
    conn = TCPAsyncSocketConnection()
    assertions = 0
    for attribute in dir(conn):
        if attribute.startswith("read_"):
            assert iscoroutinefunction(conn.__getattribute__(attribute))
            assertions += 1
    assert assertions > 0, "None of the read_* attributes were async"


def test_query_is_completely_asynchronous():
    conn = UDPAsyncSocketConnection()
    assertions = 0
    for attribute in dir(conn):
        if attribute.startswith("read_"):
            assert iscoroutinefunction(conn.__getattribute__(attribute))
            assertions += 1
    assert assertions > 0, "None of the read_* attributes were async"
