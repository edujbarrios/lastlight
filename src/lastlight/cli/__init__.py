"""Command-line interface and command handlers.

The package re-exports the historical ``lastlight.cli`` module surface so tests,
embedders and monkeypatch-based integrations keep working after the source tree
was split into subpackages.
"""

from .cli import *  # noqa: F401,F403
