from pathlib import Path
from typing import Optional

from boldi.cli import CliCtx


def docs(ctx: CliCtx):
    root: Optional[Path] = None
    for parent_dir in [ctx.cwd] + list(ctx.cwd.parents):
        if (parent_dir / "mkdocs.yml").is_file():
            root = parent_dir
            break

    if not root:
        return

    ctx.run_py("-m mkdocs build", cwd=root)
