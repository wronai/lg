"""Tests for nfo.auto (auto_log module-level patching)."""

import types
import pytest

from nfo.auto import auto_log, _should_patch
from nfo.logger import Logger
from nfo.sinks import Sink
from nfo.models import LogEntry
from nfo.decorators import set_default_logger
from nfo.logged import skip


class MemorySink(Sink):
    def __init__(self):
        self.entries: list[LogEntry] = []

    def write(self, entry: LogEntry) -> None:
        self.entries.append(entry)

    def close(self) -> None:
        self.entries.clear()


def _make_module(name: str = "test_mod", **funcs) -> types.ModuleType:
    """Create a fake module with given functions."""
    mod = types.ModuleType(name)
    mod.__name__ = name
    for fname, fn in funcs.items():
        fn.__module__ = name
        fn.__qualname__ = fname
        fn.__name__ = fname
        setattr(mod, fname, fn)
    return mod


class TestAutoLog:

    def test_patches_public_functions(self):
        sink = MemorySink()
        lgr = Logger(name="test-auto", sinks=[sink], propagate_stdlib=False)
        set_default_logger(lgr)

        def add(a, b):
            return a + b

        def mul(a, b):
            return a * b

        mod = _make_module("mymod", add=add, mul=mul)
        count = auto_log(mod)
        assert count == 2

        mod.add(1, 2)
        mod.mul(3, 4)
        assert len(sink.entries) == 2
        assert sink.entries[0].return_value == 3
        assert sink.entries[1].return_value == 12
        lgr.close()

    def test_skips_private_functions(self):
        sink = MemorySink()
        lgr = Logger(name="test-auto2", sinks=[sink], propagate_stdlib=False)
        set_default_logger(lgr)

        def public_fn():
            return 1

        def _private_fn():
            return 2

        mod = _make_module("mymod2", public_fn=public_fn, _private_fn=_private_fn)
        count = auto_log(mod)
        assert count == 1  # only public_fn

        mod.public_fn()
        assert len(sink.entries) == 1
        lgr.close()

    def test_include_private(self):
        sink = MemorySink()
        lgr = Logger(name="test-auto3", sinks=[sink], propagate_stdlib=False)
        set_default_logger(lgr)

        def public_fn():
            return 1

        def _private_fn():
            return 2

        mod = _make_module("mymod3", public_fn=public_fn, _private_fn=_private_fn)
        count = auto_log(mod, include_private=True)
        assert count == 2
        lgr.close()

    def test_catch_exceptions_mode(self):
        sink = MemorySink()
        lgr = Logger(name="test-auto4", sinks=[sink], propagate_stdlib=False)
        set_default_logger(lgr)

        def risky():
            raise ValueError("boom")

        mod = _make_module("mymod4", risky=risky)
        auto_log(mod, catch_exceptions=True, default=-1)

        result = mod.risky()
        assert result == -1  # exception caught, returns default
        assert len(sink.entries) == 1
        assert sink.entries[0].level == "ERROR"
        assert sink.entries[0].exception_type == "ValueError"
        lgr.close()

    def test_does_not_double_wrap(self):
        sink = MemorySink()
        lgr = Logger(name="test-auto5", sinks=[sink], propagate_stdlib=False)
        set_default_logger(lgr)

        def fn():
            return 42

        mod = _make_module("mymod5", fn=fn)
        count1 = auto_log(mod)
        count2 = auto_log(mod)  # second call should skip already-wrapped
        assert count1 == 1
        assert count2 == 0

        mod.fn()
        assert len(sink.entries) == 1  # only one layer of wrapping
        lgr.close()

    def test_skips_imported_functions(self):
        """Functions from other modules should not be patched."""
        sink = MemorySink()
        lgr = Logger(name="test-auto6", sinks=[sink], propagate_stdlib=False)
        set_default_logger(lgr)

        def local_fn():
            return 1

        import os
        mod = _make_module("mymod6", local_fn=local_fn)
        # Manually add an imported function
        mod.path_exists = os.path.exists  # from os module

        count = auto_log(mod)
        assert count == 1  # only local_fn
        lgr.close()

    def test_skips_nfo_skip_decorated(self):
        sink = MemorySink()
        lgr = Logger(name="test-auto7", sinks=[sink], propagate_stdlib=False)
        set_default_logger(lgr)

        def tracked():
            return 1

        @skip
        def untracked():
            return 2

        mod = _make_module("mymod7", tracked=tracked, untracked=untracked)
        count = auto_log(mod)
        assert count == 1
        lgr.close()

    def test_custom_level(self):
        sink = MemorySink()
        lgr = Logger(name="test-auto8", sinks=[sink], propagate_stdlib=False)
        set_default_logger(lgr)

        def fn():
            return 1

        mod = _make_module("mymod8", fn=fn)
        auto_log(mod, level="INFO")
        mod.fn()
        assert sink.entries[0].level == "INFO"
        lgr.close()

    def test_skips_classes(self):
        """Classes should not be patched (use @logged for those)."""
        sink = MemorySink()
        lgr = Logger(name="test-auto9", sinks=[sink], propagate_stdlib=False)
        set_default_logger(lgr)

        class MyClass:
            pass

        def fn():
            return 1

        mod = _make_module("mymod9", fn=fn)
        mod.MyClass = MyClass
        MyClass.__module__ = "mymod9"

        count = auto_log(mod)
        assert count == 1  # only fn, not MyClass
        lgr.close()


class TestAutoLogByName:

    def test_patches_by_module_name(self):
        from nfo.auto import auto_log_by_name
        import sys

        sink = MemorySink()
        lgr = Logger(name="test-byname1", sinks=[sink], propagate_stdlib=False)
        set_default_logger(lgr)

        def greet(name):
            return f"hello {name}"

        mod = _make_module("test_byname_mod1", greet=greet)
        sys.modules["test_byname_mod1"] = mod

        count = auto_log_by_name("test_byname_mod1")
        assert count == 1

        mod.greet("world")
        assert len(sink.entries) == 1
        assert sink.entries[0].return_value == "hello world"

        del sys.modules["test_byname_mod1"]
        lgr.close()

    def test_skips_missing_modules(self):
        from nfo.auto import auto_log_by_name

        count = auto_log_by_name("nonexistent.module.xyz123")
        assert count == 0

    def test_multiple_modules_by_name(self):
        from nfo.auto import auto_log_by_name
        import sys

        sink = MemorySink()
        lgr = Logger(name="test-byname2", sinks=[sink], propagate_stdlib=False)
        set_default_logger(lgr)

        def fn_a():
            return "a"

        def fn_b():
            return "b"

        mod_a = _make_module("test_byname_a", fn_a=fn_a)
        mod_b = _make_module("test_byname_b", fn_b=fn_b)
        sys.modules["test_byname_a"] = mod_a
        sys.modules["test_byname_b"] = mod_b

        count = auto_log_by_name("test_byname_a", "test_byname_b")
        assert count == 2

        mod_a.fn_a()
        mod_b.fn_b()
        assert len(sink.entries) == 2

        del sys.modules["test_byname_a"]
        del sys.modules["test_byname_b"]
        lgr.close()
