"""Decorators for automatic function logging."""

from __future__ import annotations

import functools
import inspect
import random
import time
import traceback as tb_mod
from typing import Any, Callable, Dict, Optional, TypeVar, Union, overload

from nfo.models import DEFAULT_MAX_REPR_LENGTH, LogEntry

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


def _should_sample(sample_rate: Optional[float]) -> bool:
    """Return True if this call should be logged based on *sample_rate*.

    - ``None`` or ``1.0`` → always log
    - ``0.0`` → never log (except errors, handled by caller)
    - ``0.01`` → log ~1% of calls
    """
    if sample_rate is None or sample_rate >= 1.0:
        return True
    if sample_rate <= 0.0:
        return False
    return random.random() < sample_rate


def _maybe_extract(
    args: tuple,
    kwargs: dict,
    result: Any,
    extract_meta_flag: bool,
    meta_policy: Any,
) -> Optional[Dict[str, Any]]:
    """Build ``extra`` dict with metadata when *extract_meta_flag* is True.

    When *extract_meta_flag* is ``False``, falls back to the global
    ``auto_extract_meta`` setting from :func:`~nfo.configure.configure`.

    Returns ``None`` when metadata extraction is disabled.
    """
    effective = extract_meta_flag
    if not effective:
        from nfo.configure import get_global_auto_extract_meta
        effective = get_global_auto_extract_meta()
    if not effective:
        return None
    from nfo.extractors import extract_meta as _extract
    from nfo.meta import ThresholdPolicy, sizeof

    if meta_policy is None:
        from nfo.configure import get_global_meta_policy
        meta_policy = get_global_meta_policy()
    policy = meta_policy if meta_policy is not None else ThresholdPolicy()
    args_meta = []
    for arg in args:
        if policy.should_extract_meta(arg):
            meta = _extract(arg)
            args_meta.append(meta or {"type": type(arg).__name__, "size": sizeof(arg)})
        else:
            args_meta.append(repr(arg)[:256])
    kwargs_meta = {}
    for k, v in kwargs.items():
        if policy.should_extract_meta(v):
            meta = _extract(v)
            kwargs_meta[k] = meta or {"type": type(v).__name__, "size": sizeof(v)}
        else:
            kwargs_meta[k] = repr(v)[:256]
    return_meta = None
    if result is not None and policy.should_extract_return_meta(result):
        meta = _extract(result)
        return_meta = meta or {"type": type(result).__name__, "size": sizeof(result)}
    extra: Dict[str, Any] = {
        "args_meta": args_meta,
        "kwargs_meta": kwargs_meta,
        "meta_log": True,
    }
    if return_meta is not None:
        extra["return_meta"] = return_meta
    return extra


# ---------------------------------------------------------------------------
# @log_call — log entry + exit (return value or exception)
# ---------------------------------------------------------------------------

@overload
def log_call(func: F) -> F: ...

@overload
def log_call(
    *,
    level: str = "DEBUG",
    logger: Any = None,
    max_repr_length: Optional[int] = DEFAULT_MAX_REPR_LENGTH,
    extract_meta: bool = False,
    meta_policy: Any = None,
    sample_rate: Optional[float] = None,
) -> Callable[[F], F]: ...

def log_call(
    func: Optional[F] = None,
    *,
    level: str = "DEBUG",
    logger: Any = None,
    max_repr_length: Optional[int] = DEFAULT_MAX_REPR_LENGTH,
    extract_meta: bool = False,
    meta_policy: Any = None,
    sample_rate: Optional[float] = None,
) -> Any:
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

    Args:
        max_repr_length: Maximum repr length used by sink/stdout serialization.
            Set to ``None`` to disable truncation.
        extract_meta: If ``True``, large binary args are replaced with
            metadata dicts (format, size, hash) in ``entry.extra``.
        meta_policy: Optional :class:`~nfo.meta.ThresholdPolicy` controlling
            size thresholds. Only used when *extract_meta* is ``True``.
        sample_rate: Fraction of calls to log (0.0–1.0).  ``None`` or ``1.0``
            logs every call.  ``0.01`` logs ~1%.  Errors are **always** logged
            regardless of sampling.
    """

    def decorator(fn: F) -> F:
        if inspect.iscoroutinefunction(fn):
            @functools.wraps(fn)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                _logger = logger or _get_default_logger()
                start = time.perf_counter()
                try:
                    result = await fn(*args, **kwargs)
                    if not _should_sample(sample_rate):
                        return result
                    duration = (time.perf_counter() - start) * 1000
                    arg_t, kwarg_t = _arg_types(args, kwargs)
                    meta_extra = _maybe_extract(args, kwargs, result, extract_meta, meta_policy)
                    entry = LogEntry(
                        timestamp=LogEntry.now(),
                        level=level.upper(),
                        function_name=fn.__qualname__,
                        module=_module_of(fn),
                        args=() if meta_extra else args,
                        kwargs={} if meta_extra else kwargs,
                        arg_types=arg_t,
                        kwarg_types=kwarg_t,
                        return_value=None if meta_extra else result,
                        return_type=type(result).__name__,
                        duration_ms=round(duration, 3),
                        max_repr_length=max_repr_length,
                        extra=meta_extra or {},
                    )
                    _logger.emit(entry)
                    return result
                except Exception as exc:
                    # Errors are always logged regardless of sample_rate
                    duration = (time.perf_counter() - start) * 1000
                    arg_t, kwarg_t = _arg_types(args, kwargs)
                    err_extra = _maybe_extract(args, kwargs, None, extract_meta, meta_policy)
                    entry = LogEntry(
                        timestamp=LogEntry.now(),
                        level="ERROR",
                        function_name=fn.__qualname__,
                        module=_module_of(fn),
                        args=() if err_extra else args,
                        kwargs={} if err_extra else kwargs,
                        arg_types=arg_t,
                        kwarg_types=kwarg_t,
                        exception=str(exc),
                        exception_type=type(exc).__name__,
                        traceback=tb_mod.format_exc(),
                        duration_ms=round(duration, 3),
                        max_repr_length=max_repr_length,
                        extra=err_extra or {},
                    )
                    _logger.emit(entry)
                    raise
            return async_wrapper  # type: ignore[return-value]

        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            _logger = logger or _get_default_logger()
            start = time.perf_counter()
            try:
                result = fn(*args, **kwargs)
                if not _should_sample(sample_rate):
                    return result
                duration = (time.perf_counter() - start) * 1000
                arg_t, kwarg_t = _arg_types(args, kwargs)
                meta_extra = _maybe_extract(args, kwargs, result, extract_meta, meta_policy)
                entry = LogEntry(
                    timestamp=LogEntry.now(),
                    level=level.upper(),
                    function_name=fn.__qualname__,
                    module=_module_of(fn),
                    args=() if meta_extra else args,
                    kwargs={} if meta_extra else kwargs,
                    arg_types=arg_t,
                    kwarg_types=kwarg_t,
                    return_value=None if meta_extra else result,
                    return_type=type(result).__name__,
                    duration_ms=round(duration, 3),
                    max_repr_length=max_repr_length,
                    extra=meta_extra or {},
                )
                _logger.emit(entry)
                return result
            except Exception as exc:
                # Errors are always logged regardless of sample_rate
                duration = (time.perf_counter() - start) * 1000
                arg_t, kwarg_t = _arg_types(args, kwargs)
                err_extra = _maybe_extract(args, kwargs, None, extract_meta, meta_policy)
                entry = LogEntry(
                    timestamp=LogEntry.now(),
                    level="ERROR",
                    function_name=fn.__qualname__,
                    module=_module_of(fn),
                    args=() if err_extra else args,
                    kwargs={} if err_extra else kwargs,
                    arg_types=arg_t,
                    kwarg_types=kwarg_t,
                    exception=str(exc),
                    exception_type=type(exc).__name__,
                    traceback=tb_mod.format_exc(),
                    duration_ms=round(duration, 3),
                    max_repr_length=max_repr_length,
                    extra=err_extra or {},
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
def catch(
    *,
    level: str = "DEBUG",
    logger: Any = None,
    default: Any = None,
    max_repr_length: Optional[int] = DEFAULT_MAX_REPR_LENGTH,
    extract_meta: bool = False,
    meta_policy: Any = None,
    sample_rate: Optional[float] = None,
) -> Callable[[F], F]: ...

def catch(
    func: Optional[F] = None,
    *,
    level: str = "DEBUG",
    logger: Any = None,
    default: Any = None,
    max_repr_length: Optional[int] = DEFAULT_MAX_REPR_LENGTH,
    extract_meta: bool = False,
    meta_policy: Any = None,
    sample_rate: Optional[float] = None,
) -> Any:
    """
    Decorator that logs calls **and** suppresses exceptions.

    On exception the decorated function returns *default* instead of raising.
    """

    def decorator(fn: F) -> F:
        if inspect.iscoroutinefunction(fn):
            @functools.wraps(fn)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                _logger = logger or _get_default_logger()
                start = time.perf_counter()
                try:
                    result = await fn(*args, **kwargs)
                    if not _should_sample(sample_rate):
                        return result
                    duration = (time.perf_counter() - start) * 1000
                    arg_t, kwarg_t = _arg_types(args, kwargs)
                    meta_extra = _maybe_extract(args, kwargs, result, extract_meta, meta_policy)
                    entry = LogEntry(
                        timestamp=LogEntry.now(),
                        level=level.upper(),
                        function_name=fn.__qualname__,
                        module=_module_of(fn),
                        args=() if meta_extra else args,
                        kwargs={} if meta_extra else kwargs,
                        arg_types=arg_t,
                        kwarg_types=kwarg_t,
                        return_value=None if meta_extra else result,
                        return_type=type(result).__name__,
                        duration_ms=round(duration, 3),
                        max_repr_length=max_repr_length,
                        extra=meta_extra or {},
                    )
                    _logger.emit(entry)
                    return result
                except Exception as exc:
                    # Errors are always logged regardless of sample_rate
                    duration = (time.perf_counter() - start) * 1000
                    arg_t, kwarg_t = _arg_types(args, kwargs)
                    err_extra = _maybe_extract(args, kwargs, None, extract_meta, meta_policy)
                    entry = LogEntry(
                        timestamp=LogEntry.now(),
                        level="ERROR",
                        function_name=fn.__qualname__,
                        module=_module_of(fn),
                        args=() if err_extra else args,
                        kwargs={} if err_extra else kwargs,
                        arg_types=arg_t,
                        kwarg_types=kwarg_t,
                        exception=str(exc),
                        exception_type=type(exc).__name__,
                        traceback=tb_mod.format_exc(),
                        duration_ms=round(duration, 3),
                        max_repr_length=max_repr_length,
                        extra=err_extra or {},
                    )
                    _logger.emit(entry)
                    return default
            return async_wrapper  # type: ignore[return-value]

        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            _logger = logger or _get_default_logger()
            start = time.perf_counter()
            try:
                result = fn(*args, **kwargs)
                if not _should_sample(sample_rate):
                    return result
                duration = (time.perf_counter() - start) * 1000
                arg_t, kwarg_t = _arg_types(args, kwargs)
                meta_extra = _maybe_extract(args, kwargs, result, extract_meta, meta_policy)
                entry = LogEntry(
                    timestamp=LogEntry.now(),
                    level=level.upper(),
                    function_name=fn.__qualname__,
                    module=_module_of(fn),
                    args=() if meta_extra else args,
                    kwargs={} if meta_extra else kwargs,
                    arg_types=arg_t,
                    kwarg_types=kwarg_t,
                    return_value=None if meta_extra else result,
                    return_type=type(result).__name__,
                    duration_ms=round(duration, 3),
                    max_repr_length=max_repr_length,
                    extra=meta_extra or {},
                )
                _logger.emit(entry)
                return result
            except Exception as exc:
                # Errors are always logged regardless of sample_rate
                duration = (time.perf_counter() - start) * 1000
                arg_t, kwarg_t = _arg_types(args, kwargs)
                err_extra = _maybe_extract(args, kwargs, None, extract_meta, meta_policy)
                entry = LogEntry(
                    timestamp=LogEntry.now(),
                    level="ERROR",
                    function_name=fn.__qualname__,
                    module=_module_of(fn),
                    args=() if err_extra else args,
                    kwargs={} if err_extra else kwargs,
                    arg_types=arg_t,
                    kwarg_types=kwarg_t,
                    exception=str(exc),
                    exception_type=type(exc).__name__,
                    traceback=tb_mod.format_exc(),
                    duration_ms=round(duration, 3),
                    max_repr_length=max_repr_length,
                    extra=err_extra or {},
                )
                _logger.emit(entry)
                return default

        return wrapper  # type: ignore[return-value]

    if func is not None:
        return decorator(func)
    return decorator
