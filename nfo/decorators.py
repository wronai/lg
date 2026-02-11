"""Decorators for automatic function logging."""

from __future__ import annotations

import functools
import inspect
import time
import traceback as tb_mod
from typing import Any, Callable, Optional, TypeVar, overload

from nfo.models import LogEntry

F = TypeVar("F", bound=Callable[..., Any])

# ---------------------------------------------------------------------------
# Module-level default logger (lazy-initialised)
# ---------------------------------------------------------------------------

_default_logger: Optional[Any] = None  # nfo.logger.Logger


def _get_default_logger() -> Any:
    global _default_logger
    if _default_logger is None:
        from nfo.logger import Logger
        _default_logger = Logger()
    return _default_logger


def set_default_logger(logger: Any) -> None:
    """Replace the module-level default logger used by decorators."""
    global _default_logger
    _default_logger = logger


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _arg_types(args: tuple, kwargs: dict) -> tuple:
    arg_types = [type(a).__name__ for a in args]
    kwarg_types = {k: type(v).__name__ for k, v in kwargs.items()}
    return arg_types, kwarg_types


def _module_of(func: Callable) -> str:
    return getattr(func, "__module__", "") or ""


# ---------------------------------------------------------------------------
# @log_call — log entry + exit (return value or exception)
# ---------------------------------------------------------------------------

@overload
def log_call(func: F) -> F: ...

@overload
def log_call(*, level: str = "DEBUG", logger: Any = None) -> Callable[[F], F]: ...

def log_call(func: Optional[F] = None, *, level: str = "DEBUG", logger: Any = None) -> Any:
    """
    Decorator that automatically logs function calls.

    Can be used bare (``@log_call``) or with parameters
    (``@log_call(level="INFO")``).

    Logs:
    - function name, module
    - positional and keyword arguments with their types
    - return value and type
    - exception details + traceback on failure
    - wall-clock duration in milliseconds
    """

    def decorator(fn: F) -> F:
        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            _logger = logger or _get_default_logger()
            arg_t, kwarg_t = _arg_types(args, kwargs)
            start = time.perf_counter()
            try:
                result = fn(*args, **kwargs)
                duration = (time.perf_counter() - start) * 1000
                entry = LogEntry(
                    timestamp=LogEntry.now(),
                    level=level.upper(),
                    function_name=fn.__qualname__,
                    module=_module_of(fn),
                    args=args,
                    kwargs=kwargs,
                    arg_types=arg_t,
                    kwarg_types=kwarg_t,
                    return_value=result,
                    return_type=type(result).__name__,
                    duration_ms=round(duration, 3),
                )
                _logger.emit(entry)
                return result
            except Exception as exc:
                duration = (time.perf_counter() - start) * 1000
                entry = LogEntry(
                    timestamp=LogEntry.now(),
                    level="ERROR",
                    function_name=fn.__qualname__,
                    module=_module_of(fn),
                    args=args,
                    kwargs=kwargs,
                    arg_types=arg_t,
                    kwarg_types=kwarg_t,
                    exception=str(exc),
                    exception_type=type(exc).__name__,
                    traceback=tb_mod.format_exc(),
                    duration_ms=round(duration, 3),
                )
                _logger.emit(entry)
                raise

        return wrapper  # type: ignore[return-value]

    if func is not None:
        return decorator(func)
    return decorator


# ---------------------------------------------------------------------------
# @catch — like @log_call but suppresses exceptions (returns None)
# ---------------------------------------------------------------------------

@overload
def catch(func: F) -> F: ...

@overload
def catch(*, level: str = "DEBUG", logger: Any = None, default: Any = None) -> Callable[[F], F]: ...

def catch(func: Optional[F] = None, *, level: str = "DEBUG", logger: Any = None, default: Any = None) -> Any:
    """
    Decorator that logs calls **and** suppresses exceptions.

    On exception the decorated function returns *default* instead of raising.
    """

    def decorator(fn: F) -> F:
        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            _logger = logger or _get_default_logger()
            arg_t, kwarg_t = _arg_types(args, kwargs)
            start = time.perf_counter()
            try:
                result = fn(*args, **kwargs)
                duration = (time.perf_counter() - start) * 1000
                entry = LogEntry(
                    timestamp=LogEntry.now(),
                    level=level.upper(),
                    function_name=fn.__qualname__,
                    module=_module_of(fn),
                    args=args,
                    kwargs=kwargs,
                    arg_types=arg_t,
                    kwarg_types=kwarg_t,
                    return_value=result,
                    return_type=type(result).__name__,
                    duration_ms=round(duration, 3),
                )
                _logger.emit(entry)
                return result
            except Exception as exc:
                duration = (time.perf_counter() - start) * 1000
                entry = LogEntry(
                    timestamp=LogEntry.now(),
                    level="ERROR",
                    function_name=fn.__qualname__,
                    module=_module_of(fn),
                    args=args,
                    kwargs=kwargs,
                    arg_types=arg_t,
                    kwarg_types=kwarg_t,
                    exception=str(exc),
                    exception_type=type(exc).__name__,
                    traceback=tb_mod.format_exc(),
                    duration_ms=round(duration, 3),
                )
                _logger.emit(entry)
                return default

        return wrapper  # type: ignore[return-value]

    if func is not None:
        return decorator(func)
    return decorator
