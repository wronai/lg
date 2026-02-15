"""Tests for nfo.click — Click integration (NfoGroup, NfoCommand, nfo_options)."""

import io

import click
import pytest
from click.testing import CliRunner

from nfo.click import NfoGroup, NfoCommand, nfo_options
from nfo.terminal import TerminalSink
from nfo.logger import Logger


# ---------------------------------------------------------------------------
# NfoGroup
# ---------------------------------------------------------------------------

class TestNfoGroup:

    def test_group_logs_command(self):
        """NfoGroup should emit a log entry when a command completes."""
        entries = []

        class CaptureSink:
            def write(self, entry):
                entries.append(entry)
            def close(self):
                pass

        logger = Logger(name="test", sinks=[CaptureSink()], propagate_stdlib=False)

        @click.group(cls=NfoGroup, nfo_logger=logger)
        def cli():
            pass

        @cli.command()
        @click.argument("name")
        def greet(name):
            click.echo(f"Hello, {name}!")

        runner = CliRunner()
        result = runner.invoke(cli, ["greet", "World"])
        assert result.exit_code == 0
        assert "Hello, World!" in result.output
        assert len(entries) >= 1
        assert entries[-1].level == "INFO"

    def test_group_logs_error(self):
        """NfoGroup should log ERROR when a command raises."""
        entries = []

        class CaptureSink:
            def write(self, entry):
                entries.append(entry)
            def close(self):
                pass

        logger = Logger(name="test", sinks=[CaptureSink()], propagate_stdlib=False)

        @click.group(cls=NfoGroup, nfo_logger=logger)
        def cli():
            pass

        @cli.command()
        def fail():
            raise RuntimeError("boom")

        runner = CliRunner()
        result = runner.invoke(cli, ["fail"])
        assert result.exit_code != 0
        error_entries = [e for e in entries if e.level == "ERROR"]
        assert len(error_entries) >= 1
        assert error_entries[0].exception_type == "RuntimeError"

    def test_group_duration_recorded(self):
        """Duration should be recorded in the log entry."""
        entries = []

        class CaptureSink:
            def write(self, entry):
                entries.append(entry)
            def close(self):
                pass

        logger = Logger(name="test", sinks=[CaptureSink()], propagate_stdlib=False)

        @click.group(cls=NfoGroup, nfo_logger=logger)
        def cli():
            pass

        @cli.command()
        def fast():
            click.echo("done")

        runner = CliRunner()
        runner.invoke(cli, ["fast"])
        assert entries[-1].duration_ms is not None
        assert entries[-1].duration_ms >= 0

    def test_group_filters_nfo_params(self):
        """nfo_* params should not appear in logged kwargs."""
        entries = []

        class CaptureSink:
            def write(self, entry):
                entries.append(entry)
            def close(self):
                pass

        logger = Logger(name="test", sinks=[CaptureSink()], propagate_stdlib=False)

        @click.group(cls=NfoGroup, nfo_logger=logger)
        @nfo_options
        def cli(**kwargs):
            pass

        @cli.command()
        def hello():
            click.echo("hi")

        runner = CliRunner()
        runner.invoke(cli, ["--nfo-format", "ascii", "hello"])
        for e in entries:
            for k in e.kwargs:
                assert not k.startswith("nfo_")


# ---------------------------------------------------------------------------
# NfoCommand
# ---------------------------------------------------------------------------

class TestNfoCommand:

    def test_command_logs_invocation(self):
        """NfoCommand should log its own invocation."""
        entries = []

        class CaptureSink:
            def write(self, entry):
                entries.append(entry)
            def close(self):
                pass

        logger = Logger(name="test", sinks=[CaptureSink()], propagate_stdlib=False)

        @click.command(cls=NfoCommand)
        @click.argument("target")
        @click.pass_context
        def deploy(ctx, target):
            ctx.ensure_object(dict)["nfo_logger"] = logger
            click.echo(f"Deploying {target}")

        runner = CliRunner()
        result = runner.invoke(deploy, ["prod"])
        assert result.exit_code == 0
        assert "Deploying prod" in result.output

    def test_command_logs_error(self):
        """NfoCommand should log ERROR on exception."""
        entries = []

        class CaptureSink:
            def write(self, entry):
                entries.append(entry)
            def close(self):
                pass

        logger = Logger(name="test", sinks=[CaptureSink()], propagate_stdlib=False)

        @click.group(cls=NfoGroup, nfo_logger=logger)
        def cli():
            pass

        @cli.command()
        def boom():
            raise ValueError("kaboom")

        runner = CliRunner()
        result = runner.invoke(cli, ["boom"])
        assert result.exit_code != 0
        error_entries = [e for e in entries if e.level == "ERROR"]
        assert len(error_entries) >= 1


# ---------------------------------------------------------------------------
# nfo_options decorator
# ---------------------------------------------------------------------------

class TestNfoOptions:

    def test_adds_three_options(self):
        """nfo_options should add --nfo-sink, --nfo-format, --nfo-level."""

        @click.command()
        @nfo_options
        def cmd(nfo_sink, nfo_format, nfo_level):
            click.echo(f"{nfo_sink}|{nfo_format}|{nfo_level}")

        runner = CliRunner()
        result = runner.invoke(cmd, [
            "--nfo-sink", "sqlite:test.db",
            "--nfo-format", "toon",
            "--nfo-level", "INFO",
        ])
        assert result.exit_code == 0
        assert "sqlite:test.db|toon|INFO" in result.output

    def test_defaults(self):
        """Defaults: empty sink, color format, DEBUG level."""

        @click.command()
        @nfo_options
        def cmd(nfo_sink, nfo_format, nfo_level):
            click.echo(f"{nfo_sink}|{nfo_format}|{nfo_level}")

        runner = CliRunner()
        result = runner.invoke(cmd, [])
        assert result.exit_code == 0
        assert "|color|DEBUG" in result.output

    def test_format_choices(self):
        """Invalid format should be rejected."""

        @click.command()
        @nfo_options
        def cmd(**kwargs):
            pass

        runner = CliRunner()
        result = runner.invoke(cmd, ["--nfo-format", "invalid"])
        assert result.exit_code != 0

    def test_level_choices(self):
        """Invalid level should be rejected."""

        @click.command()
        @nfo_options
        def cmd(**kwargs):
            pass

        runner = CliRunner()
        result = runner.invoke(cmd, ["--nfo-level", "TRACE"])
        assert result.exit_code != 0


# ---------------------------------------------------------------------------
# configure() terminal sink spec
# ---------------------------------------------------------------------------

class TestConfigureTerminalSpec:

    def test_parse_terminal_color(self):
        from nfo.configure import _parse_sink_spec
        sink = _parse_sink_spec("terminal:color")
        assert isinstance(sink, TerminalSink)
        assert sink.format == "color"

    def test_parse_terminal_markdown(self):
        from nfo.configure import _parse_sink_spec
        sink = _parse_sink_spec("terminal:markdown")
        assert isinstance(sink, TerminalSink)
        assert sink.format == "markdown"

    def test_parse_terminal_toon(self):
        from nfo.configure import _parse_sink_spec
        sink = _parse_sink_spec("terminal:toon")
        assert isinstance(sink, TerminalSink)
        assert sink.format == "toon"

    def test_parse_terminal_table(self):
        from nfo.configure import _parse_sink_spec
        sink = _parse_sink_spec("terminal:table")
        assert isinstance(sink, TerminalSink)
        assert sink.format == "table"

    def test_parse_terminal_ascii(self):
        from nfo.configure import _parse_sink_spec
        sink = _parse_sink_spec("terminal:ascii")
        assert isinstance(sink, TerminalSink)
        assert sink.format == "ascii"

    def test_parse_terminal_unknown_defaults_to_color(self):
        from nfo.configure import _parse_sink_spec
        sink = _parse_sink_spec("terminal:unknown_fmt")
        assert isinstance(sink, TerminalSink)
        assert sink.format == "color"
