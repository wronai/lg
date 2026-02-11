"""
Module-level automatic logging — one call to instrument everything.

Usage:
    # At the bottom of any module:
    import nfo
    nfo.auto_log()  # wraps ALL functions in this module with @log_call

    # Or target a specific module:
    import myapp.core
    nfo.auto_log(myapp.core)

    # Or in __init__.py for an entire package:
    import nfo
    from myapp import api, core, models
    nfo.auto_log(api, core, models)

This eliminates the need to decorate every function individually.
Functions starting with '_' are skipped. Use @nfo.skip to exclude specific public functions.
"""

from __future__ import annotations

import inspect
import sys
import types
from typing import Any, Optional, Sequence, Union

from nfo.decorators import log_call


def _should_patch(name: str, obj: Any, module_name: str, include_private: bool = False) -> bool:
    """Determine if an object should be auto-patched with logging."""
    if name.startswith("__") and name.endswith("__"):
        return False
    if name.startswith("_") and not include_private:
        return False
    if getattr(obj, "_nfo_skip", False):
        return False
    if getattr(obj, "_nfo_wrapped", False):
        return False
    if not callable(obj):
        return False
    # Only patch functions/methods defined in this module
    obj_module = getattr(obj, "__module__", None)
    if obj_module and obj_module != module_name:
        return False
    # Skip classes (use @logged for those)
    if isinstance(obj, type):
        return False
    # Skip non-function callables (e.g. functools.partial)
    if not isinstance(obj, (types.FunctionType, types.MethodType)):
        return False
    return True


def auto_log(
    *modules: types.ModuleType,
    level: str = "DEBUG",
    catch_exceptions: bool = False,
    default: Any = None,
    include_private: bool = False,
    logger: Any = None,
) -> int:
    """
    Automatically wrap all functions in one or more modules with logging.

    Call with no arguments to patch the calling module:
        nfo.auto_log()

    Call with module references to patch specific modules:
        nfo.auto_log(myapp.api, myapp.core)

    Args:
        *modules: Modules to patch. If empty, patches the caller's module.
        level: Log level for successful calls (default: DEBUG).
        catch_exceptions: If True, use @catch (suppress exceptions) instead of @log_call.
        default: Default return value when catch_exceptions=True and exception occurs.
        include_private: If True, also wrap functions starting with '_' (except '__dunder__').
        logger: Custom Logger instance to use.

    Returns:
        Number of functions wrapped.

    Examples:
        # Patch current module (put at bottom of file):
        import nfo
        nfo.auto_log()

        # Patch with exception catching (all functions become safe):
        nfo.auto_log(catch_exceptions=True, default=None)

        # Patch specific modules:
        import myapp.api
        import myapp.core
        nfo.auto_log(myapp.api, myapp.core, level="INFO")
    """
    from nfo.decorators import catch as catch_decorator

    # If no modules specified, patch the caller's module
    if not modules:
        frame = inspect.stack()[1]
        caller_module_name = frame[0].f_globals.get("__name__")
        if caller_module_name and caller_module_name in sys.modules:
            modules = (sys.modules[caller_module_name],)
        else:
            return 0

    wrapper = (
        catch_decorator(level=level, logger=logger, default=default)
        if catch_exceptions
        else log_call(level=level, logger=logger)
    )

    count = 0
    for mod in modules:
        if not isinstance(mod, types.ModuleType):
            continue
        mod_name = getattr(mod, "__name__", "")
        for name in list(vars(mod)):
            obj = getattr(mod, name, None)
            if not _should_patch(name, obj, mod_name, include_private=include_private):
                continue

            wrapped = wrapper(obj)
            wrapped._nfo_wrapped = True  # type: ignore[attr-defined]
            setattr(mod, name, wrapped)
            count += 1

    return count


def auto_log_by_name(
    *module_names: str,
    level: str = "DEBUG",
    catch_exceptions: bool = False,
    default: Any = None,
    include_private: bool = False,
    logger: Any = None,
) -> int:
    """
    Like auto_log() but accepts module name strings instead of module objects.

    Only patches modules that are already imported (in sys.modules).
    Silently skips modules that haven't been imported yet.

    This is the recommended API for nfo_config.py integration files:

        from nfo import auto_log_by_name
        auto_log_by_name(
            "myapp.api",
            "myapp.core",
            "myapp.models",
            level="INFO",
        )

    Args:
        *module_names: Dotted module names to patch.
        level: Log level for successful calls.
        catch_exceptions: If True, suppress exceptions.
        default: Default return value on exception.
        include_private: Also wrap _private functions.
        logger: Custom Logger instance.

    Returns:
        Total number of functions wrapped across all modules.
    """
    resolved = []
    for name in module_names:
        mod = sys.modules.get(name)
        if mod is not None:
            resolved.append(mod)

    if not resolved:
        return 0

    return auto_log(
        *resolved,
        level=level,
        catch_exceptions=catch_exceptions,
        default=default,
        include_private=include_private,
        logger=logger,
    )
