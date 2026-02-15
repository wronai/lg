#!/usr/bin/env python3
"""Demo: using nfo.configure() with terminal sink spec in Click app.

Shows how to use configure() with 'terminal:markdown' sink spec
alongside persistent SQLite logging.

Usage:
    python demo_configure.py deploy prod --force
    python demo_configure.py migrate /tmp/test.db
"""

import click

from nfo import configure, log_call


# Configure nfo with terminal markdown output + SQLite persistence
configure(
    sinks=["terminal:markdown", "sqlite:demo_cli.db"],
    level="DEBUG",
    propagate_stdlib=False,
)


@click.group()
def cli():
    """Demo CLI using nfo.configure() with terminal sink."""
    pass


@cli.command()
@click.argument("target")
@click.option("--force", is_flag=True)
@log_call(level="INFO")
def deploy(target, force):
    """Deploy to target."""
    click.echo(f"Deploying to {target} (force={force})")
    return {"target": target, "status": "ok"}


@cli.command()
@click.argument("db_path")
@log_call(level="INFO")
def migrate(db_path):
    """Run database migration."""
    click.echo(f"Migrating {db_path}...")
    return {"migrated": True}


if __name__ == "__main__":
    cli()
