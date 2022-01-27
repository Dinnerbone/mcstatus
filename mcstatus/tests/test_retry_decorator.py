from mcstatus.utils import retry
from mcstatus.tests.test_async_pinger import async_decorator


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

    try:
        func()
    except Exception as exc:
        # We should always get the last exception on failure
        assert isinstance(exc, RuntimeError)
    else:
        assert False


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

    try:
        async_decorator(func)()
    except Exception as exc:
        # We should always get the last exception on failure
        assert isinstance(exc, RuntimeError)
    else:
        assert False
