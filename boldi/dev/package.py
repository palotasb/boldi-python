from pathlib import Path
from typing import Optional

from boldi.cli import CliCtx


def package(ctx: CliCtx):
    ctx.console.print("[green]package[/]")
    root: Optional[Path] = None
    for parent_dir in [ctx.cwd] + list(ctx.cwd.parents):
        if (parent_dir / ".git").is_dir():
            root = parent_dir
            break

    if not root:
        return

    for pkg in sorted((root / "pkg").iterdir()):
        if pkg.is_dir() and (pkg / "pyproject.toml").is_file():
            ctx.run_py("-m build --no-isolation --sdist --wheel", ["--outdir", root / "dist"], [pkg])
