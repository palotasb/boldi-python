import argparse
import functools
import os
import os.path
import re
from dataclasses import dataclass
from pathlib import Path

import tomli

from boldi.ctx import Ctx


@dataclass
class BackupSource:
    archive_name: str
    sources: list[Path]
    excludes: list[Path]


valid_archive_name_re = re.compile(r"^[\w\d_-]{1,100}$")
time_format = r"{now:%Y-%m-%d_%H-%M-%S}"


@dataclass
class Borg:
    ctx: Ctx
    repo: Path
    mount: Path
    env: dict[str, str]
    backup_sources: dict[str, BackupSource]

    def run_borg(self, *args, **kwargs):
        env = kwargs.get("env", self.env)
        for env_var, value in self.env.items():
            env.setdefault(env_var, value)

        self.ctx.run("borg", *args, env={**os.environ, **self.env}, **kwargs)

    @staticmethod
    def from_config_file(ctx: Ctx, config_file: Path) -> "Borg":
        with config_file.open("rb") as fp:
            raw_config = tomli.load(fp)

        repo = Path(raw_config["repo"])
        mount = Path(raw_config["mount"])

        backup_sources = {}
        for raw_src_name, raw_src_config in raw_config.get("backup", {}).items():
            raw_src_config.setdefault("archive_name", raw_src_name)
            archive_name = raw_src_config["archive_name"]
            assert valid_archive_name_re.match(
                archive_name
            ), f"archive name must be alphanumeric and 1-100 chars, but got: {archive_name!r}"

            assert (
                "source_dir" in raw_src_config
            ), f"backup.{raw_src_name} must contain 'source_dir', but got {raw_src_config.keys()}"
            source_dir = raw_src_config["source_dir"]
            if isinstance(source_dir, str):
                source_dirs = [Path(source_dir).expanduser()]
            elif isinstance(source_dir, list):
                source_dirs = [Path(item).expanduser() for item in source_dir]
            else:
                assert isinstance(
                    source_dir, (str, list)
                ), f"backup.{raw_src_name}.source_dir must be a string or list of strings"

            excludes = raw_src_config.get("exclude", [])
            if isinstance(excludes, str):
                excludes = [Path(excludes).expanduser() if excludes.startswith("~") else excludes]
            if isinstance(excludes, list):
                excludes = [str(Path(item).expanduser()) if item.startswith("~") else item for item in excludes]
            else:
                assert isinstance(
                    excludes, (str, list)
                ), f"backup.{raw_src_name}.excludes must be a string or list of strings"

            backup_sources[archive_name] = BackupSource(archive_name, source_dirs, excludes)

        env = raw_config.get("env", {})
        env.setdefault("BORG_REPO", str(repo))

        return Borg(
            ctx=ctx,
            repo=repo,
            mount=mount,
            env=raw_config.get("env", {}),
            backup_sources=backup_sources,
        )


def action_help(borg: Borg, parser: argparse.ArgumentParser):
    parser.print_help(borg.ctx.stderr)


def action_borg(borg: Borg, command: list[str]):
    borg.run_borg(*command)


def action_backup(borg: Borg, only: list[str], borg_args: list[str]):
    for item in only:
        assert (
            item in borg.backup_sources
        ), f"{item} is not a valid backup source (those would be: {list(borg.backup_sources.keys())})"

    for name, backup_source in borg.backup_sources.items():
        if only != [] and name not in only:
            continue

        backup_sources = backup_source.sources
        common_prefix = Path(os.path.commonpath(backup_sources))
        backup_sources = [item for item in backup_sources if item.exists()]
        backup_sources = [item.relative_to(common_prefix) for item in backup_sources]
        if backup_sources:
            borg.run_borg(
                "create",
                "--exclude-caches",
                ["--exclude", "*/.Spotlight-*"],
                ["--exclude", "*/.Trashes"],
                *[["--exclude", item] for item in backup_source.excludes],
                "--stats --verbose --progress",
                *borg_args,
                "--",
                [f"::{backup_source.archive_name}_{time_format}"],
                backup_sources,
                cwd=common_prefix,
            )


def action_mount(borg: Borg):
    borg.run_borg("mount ::", [borg.mount])


def action_umount(borg: Borg):
    borg.run_borg("umount", [borg.mount])


def main(ctx: Ctx):
    ctx = ctx or Ctx()
    parser = argparse.ArgumentParser(prog=Path(ctx.argv[0]).name, description=__doc__)
    parser.set_defaults(action=functools.partial(action_help, parser=parser))

    parser.add_argument("--config", "-c", default="~/.config/boldibackup.toml", help="Backup config file")

    subparsers = parser.add_subparsers(title="Command")

    subparsers.add_parser("help", help="Show this help message and exit")

    subparser_borg = subparsers.add_parser("borg", help="Run a command with `borg`")
    subparser_borg.set_defaults(action=action_borg)
    subparser_borg.add_argument("command", nargs="*", help="Borg command to execute")

    subparser_backup = subparsers.add_parser("backup", help="Perform a backup")
    subparser_backup.set_defaults(action=action_backup)
    subparser_backup.add_argument(
        "--only",
        "-i",
        default=[],
        action="append",
        help="Only back up the listed backup sources",
    )
    subparser_backup.add_argument("borg_args", nargs="*", help="Additional `borg create` arguments")

    subparser_mount = subparsers.add_parser("mount", help="Run `borg mount`")
    subparser_mount.set_defaults(action=action_mount)

    subparser_umount = subparsers.add_parser("umount", help="Run `borg umount`")
    subparser_umount.set_defaults(action=action_umount)

    parsed_args = vars(parser.parse_args(ctx.argv[1:]))
    config_file = Path(parsed_args.pop("config")).expanduser()
    borg = Borg.from_config_file(ctx, config_file)
    action = parsed_args.pop("action")
    action(borg, **parsed_args)


if __name__ == "__main__":
    main(Ctx())
