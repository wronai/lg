"""Dedicated decorator for logging metadata instead of raw binary data.

``@meta_log`` is purpose-built for functions that process binary payloads
(images, audio, ML tensors).  It never logs raw ``bytes``/``bytearray``
above the configured threshold — only lightweight metadata (format, size,
hash, dimensions, entropy).

Supports both sync and async functions.
"""

from __future__ import annotations

import functools
import inspect
import time
import traceback as tb_mod
from typing import Any, Callable, Dict, Optional, TypeVar

from nfo.decorators import _should_sample
from nfo.extractors import extract_meta
from nfo.meta import ThresholdPolicy, sizeof
from nfo.models import LogEntry

F = TypeVar("F", bound=Callable[..., Any])

DEFAULT_POLICY = ThresholdPolicy()


def _extract_args_meta(
    args: tuple,
    param_names: list,
    policy: ThresholdPolicy,
    extract_fields: Optional[Dict[str, Callable]] = None,
) -> list:
    """Build metadata list for positional arguments."""
    result = []
    for i, arg in enumerate(args):
        name = param_names[i] if i < len(param_names) else f"arg_{i}"
        if extract_fields and name in extract_fields:
            result.append({name: extract_fields[name](arg)})
        elif policy.should_extract_meta(arg):
            meta = extract_meta(arg)
            result.append(
                {name: meta or {"type": type(arg).__name__, "size": sizeof(arg)}}
            )
        else:
            result.append({name: repr(arg)[:256]})
    return result


def _extract_kwargs_meta(
    kwargs: dict,
    policy: ThresholdPolicy,
    extract_fields: Optional[Dict[str, Callable]] = None,
) -> dict:
    """Build metadata dict for keyword arguments."""
    result = {}
    for key, val in kwargs.items():
        if extract_fields and key in extract_fields:
            result[key] = extract_fields[key](val)
        elif policy.should_extract_meta(val):
            meta = extract_meta(val)
            result[key] = meta or {"type": type(val).__name__, "size": sizeof(val)}
        else:
            result[key] = repr(val)[:256]
    return result


def _extract_return_meta(value: Any, policy: ThresholdPolicy) -> Any:
    """Build metadata for the return value."""
    if policy.should_extract_return_meta(value):
        meta = extract_meta(value)
        return meta or {"type": type(value).__name__, "size": sizeof(value)}
    return repr(value)[:256]


def _emit(entry: LogEntry, logger: Any) -> None:
    from nfo.decorators import _get_default_logger

    (logger or _get_default_logger()).emit(entry)


def meta_log(
    func: Optional[Callable] = None,
    *,
    level: str = "DEBUG",
    policy: Optional[ThresholdPolicy] = None,
    extract_fields: Optional[Dict[str, Callable]] = None,
    logger: Any = None,
    sample_rate: Optional[float] = None,
) -> Any:
    """Decorator that logs metadata instead of raw binary data.

    Unlike ``@log_call``, this decorator:

    - Automatically detects binary payloads and extracts metadata
    - Never stores raw ``bytes``/``bytearray`` above the threshold
    - Adds hash, format, dimensions, entropy to ``entry.extra``

    Args:
        level: Log level string (default ``"DEBUG"``).
        policy: :class:`ThresholdPolicy` governing size thresholds.
        extract_fields: Dict mapping argument *name* → custom extractor callable.
            E.g. ``{"image": lambda img: {"w": img.width, "h": img.height}}``.
        logger: Optional nfo Logger instance (uses default if ``None``).
        sample_rate: Fraction of calls to log (0.0–1.0).  ``None`` or ``1.0``
            logs every call.  Errors are **always** logged.
    """
    _policy = policy or DEFAULT_POLICY

    def decorator(fn: Callable) -> Callable:
        sig = inspect.signature(fn)
        param_names = list(sig.parameters.keys())

        if inspect.iscoroutinefunction(fn):

            @functools.wraps(fn)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                start = time.perf_counter()

                try:
                    result = await fn(*args, **kwargs)
                    if not _should_sample(sample_rate):
                        return result
                    duration = (time.perf_counter() - start) * 1000
                    args_meta = _extract_args_meta(args, param_names, _policy, extract_fields)
                    kwargs_meta = _extract_kwargs_meta(kwargs, _policy, extract_fields)
                    return_meta = _extract_return_meta(result, _policy)

                    entry = LogEntry(
                        timestamp=LogEntry.now(),
                        level=level.upper(),
                        function_name=fn.__qualname__,
                        module=getattr(fn, "__module__", "") or "",
                        args=(),
                        kwargs={},
                        arg_types=[type(a).__name__ for a in args],
                        kwarg_types={k: type(v).__name__ for k, v in kwargs.items()},
                        duration_ms=round(duration, 3),
                        extra={
                            "args_meta": args_meta,
                            "kwargs_meta": kwargs_meta,
                            "return_meta": return_meta,
                            "meta_log": True,
                        },
                    )
                    _emit(entry, logger)
                    return result

                except Exception as exc:
                    # Errors are always logged regardless of sample_rate
                    duration = (time.perf_counter() - start) * 1000
                    args_meta = _extract_args_meta(args, param_names, _policy, extract_fields)
                    kwargs_meta = _extract_kwargs_meta(kwargs, _policy, extract_fields)
                    entry = LogEntry(
                        timestamp=LogEntry.now(),
                        level="ERROR",
                        function_name=fn.__qualname__,
                        module=getattr(fn, "__module__", "") or "",
                        args=(),
                        kwargs={},
                        arg_types=[type(a).__name__ for a in args],
                        kwarg_types={k: type(v).__name__ for k, v in kwargs.items()},
                        exception=str(exc),
                        exception_type=type(exc).__name__,
                        traceback=tb_mod.format_exc(),
                        duration_ms=round(duration, 3),
                        extra={
                            "args_meta": args_meta,
                            "kwargs_meta": kwargs_meta,
                            "meta_log": True,
                        },
                    )
                    _emit(entry, logger)
                    raise

            return async_wrapper

        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start = time.perf_counter()

            try:
                result = fn(*args, **kwargs)
                if not _should_sample(sample_rate):
                    return result
                duration = (time.perf_counter() - start) * 1000
                args_meta = _extract_args_meta(args, param_names, _policy, extract_fields)
                kwargs_meta = _extract_kwargs_meta(kwargs, _policy, extract_fields)
                return_meta = _extract_return_meta(result, _policy)

                entry = LogEntry(
                    timestamp=LogEntry.now(),
                    level=level.upper(),
                    function_name=fn.__qualname__,
                    module=getattr(fn, "__module__", "") or "",
                    args=(),
                    kwargs={},
                    arg_types=[type(a).__name__ for a in args],
                    kwarg_types={k: type(v).__name__ for k, v in kwargs.items()},
                    duration_ms=round(duration, 3),
                    extra={
                        "args_meta": args_meta,
                        "kwargs_meta": kwargs_meta,
                        "return_meta": return_meta,
                        "meta_log": True,
                    },
                )
                _emit(entry, logger)
                return result

            except Exception as exc:
                # Errors are always logged regardless of sample_rate
                duration = (time.perf_counter() - start) * 1000
                args_meta = _extract_args_meta(args, param_names, _policy, extract_fields)
                kwargs_meta = _extract_kwargs_meta(kwargs, _policy, extract_fields)
                entry = LogEntry(
                    timestamp=LogEntry.now(),
                    level="ERROR",
                    function_name=fn.__qualname__,
                    module=getattr(fn, "__module__", "") or "",
                    args=(),
                    kwargs={},
                    arg_types=[type(a).__name__ for a in args],
                    kwarg_types={k: type(v).__name__ for k, v in kwargs.items()},
                    exception=str(exc),
                    exception_type=type(exc).__name__,
                    traceback=tb_mod.format_exc(),
                    duration_ms=round(duration, 3),
                    extra={
                        "args_meta": args_meta,
                        "kwargs_meta": kwargs_meta,
                        "meta_log": True,
                    },
                )
                _emit(entry, logger)
                raise

        return wrapper

    if func is not None:
        return decorator(func)
    return decorator
