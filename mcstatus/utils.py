from __future__ import annotations

import asyncio
import warnings
from functools import wraps
from typing import Callable, Tuple, Type


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


def deprecated(replacement: str = None, version: str = None, msg: str = None):
    def decorate(func: Callable) -> Callable:
        # Construct and send the warning message
        name = getattr(func, "__qualname__", func.__name__)
        warn_message = f"'{name}' is deprecated and will be removed"
        if version is not None:
            warn_message += f" in {version}"
        if replacement is not None:
            warn_message += f", use '{replacement}' instead"
        warn_message += "."
        if msg is not None:
            warn_message += f" ({msg})"

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            warnings.warn(warn_message)
            return func(*args, **kwargs)

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            warnings.warn(warn_message)
            return await func(*args, **kwargs)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorate
