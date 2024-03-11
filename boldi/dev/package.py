from pathlib import Path
from typing import List, Optional

from boldi.cli import CliCtx


def package(ctx: CliCtx, only_include: List[str]):
    include_set = set(only_include)
    ctx.console.print("[green]package[/]")
    root: Optional[Path] = None
    for parent_dir in [ctx.cwd] + list(ctx.cwd.parents):
        if (parent_dir / ".git").is_dir():
            root = parent_dir
            break

    if not root:
        return

    for pkg in sorted((root / "pkg").iterdir()):
        if include_set and pkg.name not in include_set:
            continue

        if pkg.is_dir() and (pkg / "pyproject.toml").is_file():
            ctx.run_py("-m build --no-isolation --sdist --wheel", ["--outdir", root / "dist"], cwd=pkg)
