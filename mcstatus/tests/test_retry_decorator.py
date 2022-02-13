import pytest

from mcstatus.tests.test_async_pinger import async_decorator
from mcstatus.utils import retry


def test_sync_success():
    x = -1

    @retry(tries=2)
    def func():
        nonlocal x
        x += 1
        return 5 / x

    y = func()
    assert x == 1
    assert y == 5


def test_sync_fail():
    x = -1

    @retry(tries=2)
    def func():
        nonlocal x
        x += 1
        if x == 0:
            raise OSError("First error")
        elif x == 1:
            raise RuntimeError("Second error")

    # We should get the last exception on failure (not OSError)
    with pytest.raises(RuntimeError):
        func()


def test_async_success():
    x = -1

    @retry(tries=2)
    async def func():
        nonlocal x
        x += 1
        return 5 / x

    y = async_decorator(func)()
    assert x == 1
    assert y == 5


def test_async_fail():
    x = -1

    @retry(tries=2)
    async def func():
        nonlocal x
        x += 1
        if x == 0:
            raise OSError("First error")
        elif x == 1:
            raise RuntimeError("Second error")

    # We should get the last exception on failure (not OSError)
    with pytest.raises(RuntimeError):
        async_decorator(func)()
