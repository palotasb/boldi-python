import argparse
import contextlib
import os
import shlex
import stat
import subprocess
import sys
import traceback
from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, TextIO, Union

import rich
import rich.console
import rich.theme
import rich.traceback

FILE = Path(__file__).absolute()

HOOK_TEMPLATE = R"""#!/bin/sh
set -eu

sys_exe={sys_exe}
if command -v "$sys_exe" 1>/dev/null 2>&1 ; then
    exec "$sys_exe" {pygithooks} run {hook} -- "$@"
fi

echo "pygithooks: python ($sys_exe) not found, no hooks running" 1>&2
exit 0
"""

_THEME = rich.theme.Theme(
    {
        "info": "blue",
        "pass": "green",
        "PASS": "bold green",
        "warn": "yellow",
        "WARN": "bold yellow",
        "fail": "red",
        "FAIL": "bold bright_red",
        "traceback.border": "yellow",
    }
)

_PGH = "[dim bold]pygithooks[/dim bold]:"


def split_args(*arg_groups: Union[str, List[Any]]) -> List[str]:
    return [str(sub_arg) for args in arg_groups for sub_arg in (shlex.split(args) if isinstance(args, str) else args)]


class PyGitHooksUsageError(Exception):
    pass


@dataclass
class Ctx:
    stack: contextlib.ExitStack = field(default_factory=contextlib.ExitStack)
    argv: List[str] = field(default_factory=lambda: sys.argv)
    cwd: Path = field(default_factory=Path.cwd)
    env: Dict[str, str] = field(default_factory=lambda: dict(os.environ))
    stdin: TextIO = field(default_factory=lambda: sys.stdin)
    stdout: TextIO = field(default_factory=lambda: sys.stdout)
    stderr: TextIO = field(default_factory=lambda: sys.stderr)
    console: rich.console.Console = field(
        default_factory=lambda: rich.console.Console(file=sys.stderr, theme=_THEME, highlight=False)
    )
    verbose: bool = True

    def msg(self, *args, **kwargs):
        self.console.print(_PGH, *args, **kwargs)

    def out(self, *args, **kwargs):
        kwargs.setdefault("file", self.stderr)
        rich.print(*args, **kwargs)

    def run(self, *args: Union[str, List[Any]], **kwargs) -> subprocess.CompletedProcess:
        kwargs.setdefault("check", True)
        kwargs.setdefault("text", True)
        kwargs.setdefault("cwd", self.cwd)
        kwargs.setdefault("env", self.env)
        if not kwargs.get("capture_output"):
            kwargs.setdefault("stdin", self.stdin)
            kwargs.setdefault("stdout", self.stdout)
            kwargs.setdefault("stderr", self.stderr)
        args_list = split_args(*args)
        return subprocess.run(args_list, **kwargs)


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
    completed_process: Optional[subprocess.CompletedProcess]

    @property
    def skipped(self) -> bool:
        return self.completed_process is None

    @property
    def passed(self) -> bool:
        return self.completed_process is not None and self.completed_process.returncode == 0


# https://git-scm.com/docs/githooks#_hooks
GIT_HOOKS: Dict[str, GitHook] = {
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
    ctx: Ctx
    parser: argparse.ArgumentParser = field(init=False)
    verbose: bool = field(init=False)
    git_repo: Path = field(init=False)
    git_dir: Path = field(init=False)
    pygithooks_path: Path = field(init=False)
    action: Callable = field(init=False)
    args: Dict[str, Any] = field(init=False)

    def __post_init__(self) -> None:
        self.parser = argparse.ArgumentParser(
            Path(self.ctx.argv[0]).name,
            description="TODO",
            allow_abbrev=False,
        )
        self.parser.set_defaults(action=self.help)
        self.parser.add_argument(
            "-v",
            "--verbose",
            action="store_true",
            default=("VERBOSE" in self.ctx.env),
            help="more verbose output",
        )
        self.parser.add_argument(
            "-C",
            "--chdir",
            metavar="DIR",
            type=Path,
            help="change the current working directory to DIR",
        )
        self.parser.add_argument(
            "-g",
            "--git-repo",
            metavar="DIR",
            type=Path,
            help="use DIR as the git repo instead of the working directory",
        )
        self.parser.add_argument("-G", "--git-dir", metavar="DIR", type=Path, help="use DIR as the .git directory")
        subparsers = self.parser.add_subparsers(title="Commands")

        parser_run = subparsers.add_parser(
            "run",
            description="Run a Git hook",
            help="Run a Git hook",
        )
        parser_run.set_defaults(action=self.run)
        parser_run.add_argument("hook", choices=GIT_HOOKS.keys(), help="Hook name as defined by Git")
        parser_run.add_argument("args", nargs="*", help="standard git hook arguments")

        parser_install = subparsers.add_parser(
            "install",
            description="Install pygithooks in Git project",
            help="Install pygithooks in Git project",
        )
        parser_install.set_defaults(action=self.install)

        self.args = vars(self.parser.parse_args(self.ctx.argv[1:]))

        self.ctx.verbose = self.args.pop("verbose")
        if self.ctx.verbose:
            self.ctx.msg("running in verbose mode")

        chdir: Path
        if chdir := self.args.pop("chdir", None):
            chdir = chdir.absolute()
            if chdir.is_dir():
                self.ctx.cwd = chdir
                self.ctx.stack.enter_context(contextlib.chdir(chdir))
            else:
                raise PyGitHooksUsageError(
                    f"not a directory: {chdir}",
                    "`cd` into a directory and omit the `--chdir DIR` option, or choose a valid DIR value.",
                )
        if self.ctx.verbose:
            self.ctx.msg("cwd:", self.ctx.cwd)

        git_repo: Path | None = self.args.pop("git_repo", None)
        self.git_repo = git_repo if git_repo else self._default_git_repo()
        if self.ctx.verbose:
            self.ctx.msg("git repo:", self.git_repo)

        git_dir: Path | None = self.args.pop("git_dir", None)
        self.git_dir = git_dir if git_dir else self.git_repo / ".git"
        if self.ctx.verbose:
            self.ctx.msg("git dir:", self.git_dir)

        self.pygithooks_path = self.git_repo / ".pygithooks"

        self.action = self.args.pop("action")

    def _default_git_repo(self) -> Path:
        for path in [self.ctx.cwd] + list(self.ctx.cwd.parents):
            if (path / ".git").is_dir():
                return path

        raise PyGitHooksUsageError(
            f"Could not find a git repo here: {self.ctx.cwd}",
            "`cd` into a git repo, or use one of these CLI options: `--chdir DIR`, `--git-repo DIR`.",
        )

    def main(self) -> None:
        self.action(**self.args)

    def help(self):
        self.parser.print_help(self.ctx.stderr)

    def _run_git_hook_script(self, git_hook_script: GitHookScript, args: List[str]) -> CompletedGitHookScript:
        try:
            python_bin_path = Path(sys.executable).parent.resolve().as_posix()
            cmd: List[Union[str, Path]] = []
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
                    self.ctx.msg(
                        f"found {git_hook_script.name}, but it isn't executable, so it will be skipped.",
                        style="info",
                    )
                return CompletedGitHookScript(git_hook_script, None)

            completed_process = self.ctx.run(
                cmd + args,
                check=False,
                capture_output=True,
                cwd=self.git_repo,
                env={
                    **self.ctx.env,
                    "PATH": os.pathsep.join([python_bin_path, self.ctx.env["PATH"]]),
                },
            )
            return CompletedGitHookScript(git_hook_script, completed_process)
        except OSError as err:
            self.ctx.msg(err)
            return CompletedGitHookScript(git_hook_script, None)

    def run(self, *, hook: str, args: List[str]):
        results: List[CompletedGitHookScript] = []
        git_hook_scripts = list(self.git_hook_scripts(GIT_HOOKS[hook]))
        if not git_hook_scripts:
            return

        self.ctx.msg(f"[bold]{hook}[/bold] hooks running...", style="info")

        for git_hook_script in git_hook_scripts:
            # self.ctx.msg(f"running hook [bold]{git_hook_script.name}[/bold]:", style="info")
            result = self._run_git_hook_script(git_hook_script, args)
            results.append(result)

            if result.passed:
                self.ctx.msg(f"[bold]{git_hook_script.name}[/bold]: [bold]PASSED[/bold]", style="pass")
            elif result.skipped:
                self.ctx.msg(f"[bold]{git_hook_script.name}[/bold]: [bold]SKIPPED[/bold]", style="warn")
            else:
                self.ctx.msg(f"[bold]{git_hook_script.name}[/bold]: [bold]FAILED[/bold]", style="fail")

            if result.completed_process:
                self.ctx.stderr.write(result.completed_process.stderr)
                self.ctx.stdout.write(result.completed_process.stdout)

        # self.ctx.msg(f"finished running [bold]{hook}[/bold] hooks.", style="info")
        all_passed = all(result.passed or result.skipped for result in results)
        any_passed = any(result.passed for result in results)
        if any_passed and all_passed:
            self.ctx.msg(f"{hook} hooks PASSED", style="PASS")
            sys.exit(0)
        elif all_passed:
            self.ctx.msg(f"{hook} hooks SKIPPED", style="WARN")
            sys.exit(0)
        else:
            self.ctx.msg(f"{hook} hooks FAILED", style="FAIL")
            sys.exit(1)

    def install(self):
        self.ctx.msg("installing pygithooks into", self.git_hooks_path)
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

    def run_git(self, *args, **kwargs) -> subprocess.CompletedProcess:
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


@contextlib.contextmanager
def basic_error_handler():
    try:
        yield
    except Exception as err:
        print(
            f"pygithooks: INTERNAL ERROR: {type(err).__name__}: {' '.join(err.args)}",
            file=sys.stderr,
        )
        print("pygithooks: This is a bug, please report it.", file=sys.stderr)
        print("pygithooks:", *traceback.format_exception(err), sep="\n", file=sys.stderr)
        sys.exit(2)


@contextlib.contextmanager
def fancy_ctx_aware_error_handler(ctx: Ctx):
    try:
        yield
    except PyGitHooksUsageError as err:
        ctx.msg("ERROR:", err.args[0], style="FAIL")
        ctx.msg("Potential solutions to this error:", err.args[1], style="warn")
        ctx.msg("Otherwise this is a bug, please report it.", style="warn")
        sys.exit(1)
    except Exception as err:
        ctx.msg(f"INTERNAL ERROR: {err.__class__.__name__}:", *err.args, style="FAIL")
        if ctx.verbose:
            ctx.msg("This is a bug, please report it.", style="fail")
            err_tb = err.__traceback__.tb_next if err.__traceback__ else None
            tb = rich.traceback.Traceback.from_exception(err.__class__, err, err_tb, extra_lines=1)
            ctx.console.print(tb)
        else:
            ctx.msg(
                "This is a bug, please report it. For details, use the `-v`/`--verbose` CLI option or set the VERBOSE env var.",
                style="fail",
            )
        sys.exit(2)


def main(stack: contextlib.ExitStack | None = None, ctx: Ctx | None = None):
    stack = stack or contextlib.ExitStack()
    with stack:
        stack.enter_context(basic_error_handler())
        ctx = ctx or Ctx(stack)
        stack.enter_context(fancy_ctx_aware_error_handler(ctx))
        assert stack is ctx.stack
        py_git_hooks = PyGitHooks(ctx)
        py_git_hooks.main()


if __name__ == "__main__":
    sys.exit(main())
