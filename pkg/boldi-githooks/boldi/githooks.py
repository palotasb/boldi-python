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


_PGH = "[dim bold]pygithooks[/]:"


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
        # GitHook("pre-push"),  # TODO pass stdin to scripts
        # GitHook("pre-receive"),  # TODO pass stdin to scripts
        GitHook("update"),
        # GitHook("proc-receive"),  # TODO implement input/output line protocol
        # GitHook("post-receive"),  # TODO pass stdin to scripts
        GitHook("post-update"),
        # GitHook("reference-transaction"),  # TODO pass stdin to scripts
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
        if not git_repo and "GIT_WORK_TREE" in ctx.env:
            git_repo = Path(ctx.env["GIT_WORK_TREE"])

        if not git_dir and "GIT_DIR" in ctx.env:
            git_dir = Path(ctx.env["GIT_DIR"])

        if not git_repo and not git_dir:
            for parent in chain([ctx.cwd], ctx.cwd.parents):
                if (parent / ".git").is_dir():
                    git_repo = parent
                    break

        if not git_repo:
            raise CliUsageException(
                "git repo not found",
                "[bold]cd[/] into a git repo [dim]or[/] set git repo path via [bold]--git-repo/-g[/] [dim]or[/] set git repo path via [bold]GIT_WORK_TREE[/]",
            )

        if not git_dir and (_git_dir := git_repo / ".git").is_dir():
            git_dir = _git_dir

        if not git_dir:
            raise CliUsageException(
                ".git dir not found",
                "[bold]cd[/] into a git repo [dim]or[/] set .git dir path via [bold]--git-dir/-G[/] [dim]or[/] set git dir path via [bold]GIT_DIR[/]",
            )

        pygithooks_path = git_repo / ".pygithooks"

        return PyGitHooks(ctx, git_repo, git_dir, pygithooks_path)

    def _run_git_hook_script(self, git_hook_script: GitHookScript, args: list[str]) -> CompletedGitHookScript:
        try:
            python_bin_path = Path(sys.executable).parent.resolve().as_posix()
            cmd: list[str | Path] = []
            if os.access(git_hook_script.path, os.F_OK | os.X_OK):
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

        self.ctx.msg_info(_PGH, f"[bold]{hook}[/] hooks running...")

        for git_hook_script in git_hook_scripts:
            # self.ctx.msg(_PGH, f"running hook [bold]{git_hook_script.name}[/]:", style="info")
            result = self._run_git_hook_script(git_hook_script, args)
            results.append(result)

            if result.passed:
                self.ctx.msg_pass(_PGH, f"[bold]{git_hook_script.name}[/]: [bold]PASSED[/]")
            elif result.skipped:
                self.ctx.msg_warn(_PGH, f"[bold]{git_hook_script.name}[/]: [bold]SKIPPED[/]")
            else:
                self.ctx.msg_fail(_PGH, f"[bold]{git_hook_script.name}[/]: [bold]FAILED[/]")

            if result.completed_process:
                self.ctx.stderr.write(result.completed_process.stderr)
                self.ctx.stdout.write(result.completed_process.stdout)

        # self.ctx.msg_info(_PGH, f"finished running [bold]{hook}[/] hooks")
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
            hook_path.chmod(hook_path.stat().st_mode | stat.S_IXUSR)

    def uninstall(self):
        self.ctx.msg_info(_PGH, "uninstalling pygithooks from", esc(self.git_hooks_path))
        for hook_path in self.installed_git_hook_paths():
            hook_path.unlink(missing_ok=True)

    def enable(self):
        self.ctx.msg_info(_PGH, "enabling pygithooks in", esc(self.git_hooks_path))
        for hook_path in self.installed_git_hook_paths():
            hook_path.chmod(hook_path.stat().st_mode | stat.S_IXUSR)

    def disable(self):
        self.ctx.msg_info(_PGH, "disabling pygithooks in", esc(self.git_hooks_path))
        for hook_path in self.installed_git_hook_paths():
            hook_path.chmod(hook_path.stat().st_mode & ~(stat.S_IEXEC | stat.S_IXGRP | stat.S_IXUSR))

    def installed_git_hook_paths(self) -> Iterable[Path]:
        for hook in GIT_HOOKS.values():
            hook_path = self.git_hooks_path / hook.name
            if hook_path.is_file():
                yield hook_path

    def git_hook_scripts(self, git_hook: GitHook) -> Iterable[GitHookScript]:
        top_level = Path(self.pygithooks_path / git_hook.name)
        if top_level.is_dir():
            yield from [
                GitHookScript(git_hook, path.relative_to(self.pygithooks_path).as_posix(), path.absolute())
                for path in sorted(top_level.iterdir())
                if path.is_file()
            ]

    @cached_property
    def git_hooks_path(self) -> Path:
        return Path(
            self.ctx.run(
                "git config --get --default",
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

    parser_install = subparsers.add_parser("install", help="Install pygithooks in Git project")
    parser_install.set_defaults(action=partial(cli_githooks_install, ctx))

    parser_uninstall = subparsers.add_parser("uninstall", help="Uninstall pygithooks from Git project")
    parser_uninstall.set_defaults(action=partial(cli_githooks_uninstall, ctx))

    parser_enable = subparsers.add_parser("enable", help="Enable installed pygithooks in Git project")
    parser_enable.set_defaults(action=partial(cli_githooks_enable, ctx))

    parser_disable = subparsers.add_parser("disable", help="Disable installed pygithooks in Git project")
    parser_disable.set_defaults(action=partial(cli_githooks_disable, ctx))

    parser_info = subparsers.add_parser("info", help="Info about pygithooks in Git project")
    parser_info.set_defaults(action=partial(cli_githooks_info, ctx))


def cli_githooks_run(ctx: CliCtx, git_repo: Path | None, git_dir: Path | None, hook: str, args: list[str]):
    PyGitHooks.create(ctx, git_repo, git_dir).run(hook=hook, args=args)


def cli_githooks_install(ctx: CliCtx, git_repo: Path | None, git_dir: Path | None):
    PyGitHooks.create(ctx, git_repo, git_dir).install()


def cli_githooks_uninstall(ctx: CliCtx, git_repo: Path | None, git_dir: Path | None):
    PyGitHooks.create(ctx, git_repo, git_dir).uninstall()


def cli_githooks_enable(ctx: CliCtx, git_repo: Path | None, git_dir: Path | None):
    PyGitHooks.create(ctx, git_repo, git_dir).enable()


def cli_githooks_disable(ctx: CliCtx, git_repo: Path | None, git_dir: Path | None):
    PyGitHooks.create(ctx, git_repo, git_dir).disable()


def cli_githooks_info(ctx: CliCtx, git_repo: Path | None, git_dir: Path | None):
    pgh = PyGitHooks.create(ctx, git_repo, git_dir)
    ctx.msg("cwd:", esc(ctx.cwd))
    ctx.msg("repo:", esc(pgh.git_repo))
    ctx.msg(".git:", esc(pgh.git_dir))
    ctx.msg("git hooks:", esc(pgh.git_hooks_path))
    ctx.msg("pygithooks:", esc(pgh.pygithooks_path))


def main(ctx: CliCtx | None = None):
    ctx = ctx or CliCtx()
    ctx.argv[1:1] = ["githooks"]
    cli_main(ctx)


if __name__ == "__main__":
    sys.exit(main())
