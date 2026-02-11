"""
One-liner project integration for nfo.

Usage in any project:

    import nfo.setup  # auto-configures logging (zero-config)

Or with explicit configuration:

    from nfo import configure
    configure(
        sinks=["sqlite:logs.db", "csv:logs.csv", "md:logs.md"],
        level="DEBUG",
        modules=["myapp.api", "myapp.core"],
    )

Or class-level decorator for SOLID compliance:

    from nfo import logged

    @logged
    class UserService:
        def create(self, name: str) -> dict: ...
        def delete(self, user_id: int) -> bool: ...
        # All public methods auto-logged

Schema for integration:
    1. Add `nfo` to dependencies
    2. Add `import nfo.setup` at project entry point (or `from nfo import configure`)
    3. Optionally configure sinks (SQLite/CSV/Markdown)
    4. Use @log_call on critical functions or @logged on classes
"""

from nfo.configure import configure as _configure

# Auto-configure with sensible defaults on import
_configure()
