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
    @retry(tries=2)
    def func():
        raise RuntimeError("This will always fail")

    try:
        func()
    except Exception as exc:
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
    @retry(tries=2)
    async def func():
        raise RuntimeError("This will always fail")

    try:
        async_decorator(func)()
    except Exception as exc:
        assert isinstance(exc, RuntimeError)
    else:
        assert False
