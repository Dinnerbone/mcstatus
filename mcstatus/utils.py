import asyncio
from typing import Callable, Tuple, Type
from functools import wraps


def retry(tries: int, exceptions: Tuple[Type[BaseException]] = (Exception,)) -> Callable:
    """
    Decorator that re-runs given function tries times if error occurs.

    The amount of tries will either be the value given to the decorator,
    or if tries is present in keyword arguments on function call, this
    specified value will take precedense.

    If the function fails even after all of the retries, raise the last
    exception that the function raised (even if the previous failures caused
    a different exception, this will only raise the last one!).
    """

    def decorate(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, tries: int = tries, **kwargs):
            last_exc: BaseException
            for _ in range(tries):
                try:
                    return await func(*args, **kwargs)
                except exceptions as exc:
                    last_exc = exc
            else:
                raise last_exc  # type: ignore # (This won't actually be unbound)

        @wraps(func)
        def sync_wrapper(*args, tries: int = tries, **kwargs):
            last_exc: BaseException
            for _ in range(tries):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    last_exc = exc
            else:
                raise last_exc  # type: ignore # (This won't actually be unbound)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorate
