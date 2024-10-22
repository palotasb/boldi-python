from __future__ import annotations

import argparse
import os
import shlex
import stat
import sys
from dataclasses import dataclass
from functools import cached_property, partial
from itertools import chain
from pathlib import Path
from subprocess import CompletedProcess
from typing import Iterable

from boldi.cli import CliCtx, CliUsageException, esc, main as cli_main

FILE = Path(__file__).absolute()

HOOK_TEMPLATE = """#!/bin/sh
set -eu

sys_exe={sys_exe}
if command -v "$sys_exe" 1>/dev/null 2>&1 ; then
    exec "$sys_exe" {pygithooks} run {hook} -- "$@"
fi

echo "pygithooks: python ($sys_exe) not found, no hooks running" 1>&2
exit 0
"""


_PGH = "[dim bold]pygithooks[/dim bold]:"


@dataclass
class GitHook:
    name: str


@dataclass
class GitHookScript:
    git_hook: GitHook
    name: str
    path: Path


@dataclass
class CompletedGitHookScript:
    git_hook_script: GitHookScript
    completed_process: CompletedProcess | None

    @property
    def skipped(self) -> bool:
        return self.completed_process is None

    @property
    def passed(self) -> bool:
        return self.completed_process is not None and self.completed_process.returncode == 0


# https://git-scm.com/docs/githooks#_hooks
GIT_HOOKS: dict[str, GitHook] = {
    git_hook.name: git_hook
    for git_hook in [
        GitHook("applypatch-msg"),
        GitHook("pre-applypatch"),
        GitHook("post-applypatch"),
        GitHook("pre-commit"),
        GitHook("pre-merge-commit"),
        GitHook("prepare-commit-msg"),
        GitHook("commit-msg"),
        GitHook("post-commit"),
        GitHook("pre-rebase"),
        GitHook("post-checkout"),
        GitHook("post-merge"),
        GitHook("pre-push"),
        GitHook("pre-receive"),
        GitHook("update"),
        # GitHook("proc-receive"), # would require implementing a line protocol
        GitHook("post-receive"),
        GitHook("post-update"),
        GitHook("reference-transaction"),
        GitHook("push-to-checkout"),
        GitHook("pre-auto-gc"),
        GitHook("post-rewrite"),
        GitHook("sendemail-validate"),
        GitHook("fsmonitor-watchman"),
        # GitHook("p4-changelist"),
        # GitHook("p4-prepare-changelist"),
        # GitHook("p4-post-changelist"),
        # GitHook("p4-pre-submit"),
        GitHook("post-index-change"),
    ]
}

_KNOWN_NOT_EXECUTABLE_FILES = (
    ".txt",
    ".md",
)


@dataclass
class PyGitHooks:
    ctx: CliCtx
    git_repo: Path
    git_dir: Path
    pygithooks_path: Path

    @staticmethod
    def create(ctx: CliCtx, git_repo: Path | None, git_dir: Path | None) -> PyGitHooks:
        def first_parent_git_repo(path: Path) -> Path:
            for path in chain([path], path.parents):
                if (path / ".git").is_dir():
                    return path

            raise CliUsageException(
                f"not a git repo: {esc(path)}",
                "[boldi]cd[/] into a git repo, or use [bold]--chdir[/] or [bold]--git-repo[/] to select one.",
            )

        git_repo = git_repo if git_repo else first_parent_git_repo(ctx.cwd)
        git_dir = git_dir if git_dir else git_repo / ".git"
        pygithooks_path = git_repo / ".pygithooks"

        return PyGitHooks(ctx, git_repo, git_dir, pygithooks_path)

    def _run_git_hook_script(self, git_hook_script: GitHookScript, args: list[str]) -> CompletedGitHookScript:
        try:
            python_bin_path = Path(sys.executable).parent.resolve().as_posix()
            cmd: list[str | Path] = []
            if git_hook_script.path.stat().st_mode & stat.S_IEXEC == stat.S_IEXEC:
                cmd = [git_hook_script.path]
            elif git_hook_script.path.suffix == ".sh":
                cmd = ["sh", git_hook_script.path]
            elif git_hook_script.path.suffix == ".bash":
                cmd = ["bash", git_hook_script.path]
            elif git_hook_script.path.suffix == ".zsh":
                cmd = ["zsh", git_hook_script.path]
            elif git_hook_script.path.suffix == ".py":
                cmd = [sys.executable, git_hook_script.path]
            else:
                if git_hook_script.path.suffix not in _KNOWN_NOT_EXECUTABLE_FILES:
                    self.ctx.msg_warn(_PGH, f"skipping non-executable [bold]{esc(git_hook_script.name)}[/]")
                return CompletedGitHookScript(git_hook_script, None)

            completed_process = self.ctx.run(
                cmd + args,
                check=False,
                capture_output=True,
                cwd=self.git_repo,
                env={
                    **self.ctx.env,
                    "PATH": os.pathsep.join([python_bin_path] + self.ctx.env["PATH"].split(os.pathsep)),
                },
            )
            return CompletedGitHookScript(git_hook_script, completed_process)
        except OSError as err:
            self.ctx.msg_warn(_PGH, err)
            return CompletedGitHookScript(git_hook_script, None)

    def run(self, *, hook: str, args: list[str]):
        results: list[CompletedGitHookScript] = []
        git_hook_scripts = list(self.git_hook_scripts(GIT_HOOKS[hook]))
        if not git_hook_scripts:
            return

        self.ctx.msg_info(_PGH, f"[bold]{hook}[/bold] hooks running...")

        for git_hook_script in git_hook_scripts:
            # self.ctx.msg(_PGH, f"running hook [bold]{git_hook_script.name}[/bold]:", style="info")
            result = self._run_git_hook_script(git_hook_script, args)
            results.append(result)

            if result.passed:
                self.ctx.msg_pass(_PGH, f"[bold]{git_hook_script.name}[/bold]: [bold]PASSED[/bold]")
            elif result.skipped:
                self.ctx.msg_warn(_PGH, f"[bold]{git_hook_script.name}[/bold]: [bold]SKIPPED[/bold]")
            else:
                self.ctx.msg_fail(_PGH, f"[bold]{git_hook_script.name}[/bold]: [bold]FAILED[/bold]")

            if result.completed_process:
                self.ctx.stderr.write(result.completed_process.stderr)
                self.ctx.stdout.write(result.completed_process.stdout)

        # self.ctx.msg_info(_PGH, f"finished running [bold]{hook}[/bold] hooks")
        all_passed = all(result.passed or result.skipped for result in results)
        any_passed = any(result.passed for result in results)
        if any_passed and all_passed:
            self.ctx.msg_PASS(_PGH, f"{hook} hooks PASSED")
            sys.exit(0)
        elif all_passed:
            self.ctx.msg_WARN(_PGH, f"{hook} hooks SKIPPED")
            sys.exit(0)
        else:
            self.ctx.msg_FAIL(_PGH, f"{hook} hooks FAILED")
            sys.exit(1)

    def install(self):
        self.ctx.msg_info(_PGH, "installing pygithooks into", esc(self.git_hooks_path))
        for hook in GIT_HOOKS.values():
            hook_path = self.git_hooks_path / hook.name
            hook_path.write_text(
                HOOK_TEMPLATE.format(
                    sys_exe=shlex.quote(sys.executable),
                    pygithooks=shlex.quote(FILE.as_posix()),
                    hook=hook.name,
                )
            )
            hook_path.chmod(hook_path.stat().st_mode | stat.S_IEXEC)

    def git_hook_scripts(self, git_hook: GitHook) -> Iterable[GitHookScript]:
        top_level = Path(self.pygithooks_path / git_hook.name)
        if top_level.is_dir():
            yield from [
                GitHookScript(git_hook, path.relative_to(self.pygithooks_path).as_posix(), path.absolute())
                for path in sorted(top_level.iterdir())
                if path.is_file()
            ]

    def run_git(self, *args, **kwargs) -> CompletedProcess:
        return self.ctx.run("git", *args, **kwargs)

    @cached_property
    def git_hooks_path(self) -> Path:
        return Path(
            self.run_git(
                "config --get --default",
                [self.git_dir / "hooks"],
                "core.hooksPath",
                capture_output=True,
            ).stdout.strip()
        )


def cli_githooks(ctx: CliCtx, subparser: argparse.ArgumentParser):
    subparser.add_argument(
        "--git-repo",
        "-g",
        metavar="DIR",
        type=Path,
        help="use DIR as the git repo working tree (default: current directory)",
    )
    subparser.add_argument("--git-dir", "-G", metavar="DIR", type=Path, help="use DIR as the .git directory")
    subparsers = subparser.add_subparsers(title="Commands")

    parser_run = subparsers.add_parser(
        "run",
        description="Run a Git hook",
        help="Run a Git hook",
    )
    parser_run.set_defaults(action=partial(cli_githooks_run, ctx))
    parser_run.add_argument("hook", choices=GIT_HOOKS.keys(), help="Hook name as defined by Git")
    parser_run.add_argument("args", nargs="*", help="standard git hook arguments")

    parser_install = subparsers.add_parser(
        "install",
        description="Install pygithooks in Git project",
        help="Install pygithooks in Git project",
    )
    parser_install.set_defaults(action=partial(cli_githooks_install, ctx))


def cli_githooks_run(ctx: CliCtx, git_repo: Path | None, git_dir: Path | None, hook: str, args: list[str]):
    PyGitHooks.create(ctx, git_repo, git_dir).run(hook=hook, args=args)


def cli_githooks_install(ctx: CliCtx, git_repo: Path | None, git_dir: Path | None):
    PyGitHooks.create(ctx, git_repo, git_dir).install()


def main(ctx: CliCtx | None = None):
    ctx = ctx or CliCtx()
    ctx.argv[1:1] = ["githooks"]
    cli_main(ctx)


if __name__ == "__main__":
    sys.exit(main())
