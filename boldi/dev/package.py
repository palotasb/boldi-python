from pathlib import Path
from typing import Optional

from boldi.cli import CliCtx


def package(ctx: CliCtx):
    ctx.console.print("[green]package[/]")
    root: Optional[Path] = None
    for parent_dir in Path(__file__).parents:
        if (parent_dir / ".git").is_dir():
            root = parent_dir
            break
    
    if not root:
        return
    
    for pkg in sorted((root / "pkg").iterdir()):
        if pkg.is_dir() and (pkg / "pyproject.toml").is_file():
            ctx.console.print("pkg:", pkg)
