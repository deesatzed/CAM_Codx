"""Local import shim for the src-layout package.

This checkout can be used without reinstalling the editable package. The shim
keeps ``python -m claw_codex_mcp`` and ``pytest`` pointed at this repository's
``src/claw_codex_mcp`` tree even if another worktree is installed globally.
"""

from __future__ import annotations

from pathlib import Path


_SRC_PACKAGE = Path(__file__).resolve().parents[1] / "src" / "claw_codex_mcp"
__path__ = [str(_SRC_PACKAGE)]

exec((_SRC_PACKAGE / "__init__.py").read_text(encoding="utf-8"), globals())
