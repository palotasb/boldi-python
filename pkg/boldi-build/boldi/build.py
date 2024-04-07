import contextlib
import json
import logging
from collections import defaultdict
from collections.abc import Coroutine
from dataclasses import dataclass, field
from functools import partial
from pathlib import Path

Target = str
Stamp = str


logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


# TODO ideas:
# - Parallelize
# - Serialize build logs https://apenwarr.ca/log/20181106


@dataclass
class BuildDB:
    targets: dict[Target, Stamp] = field(default_factory=dict)
    dependencies: defaultdict[Target, dict[Target, Stamp]] = field(
        default_factory=lambda: defaultdict(dict[Target, Stamp])
    )

    async def load(self, path: Path):
        try:
            with open(path, "r") as fp:
                build_db_json = json.load(fp)
        except (json.JSONDecodeError, OSError):
            build_db_json = {}
        build_db_json = build_db_json if isinstance(build_db_json, dict) else {}

        self.targets = build_db_json.get("targets", {})

        self.dependencies = defaultdict(dict)
        self.dependencies.update(build_db_json.get("dependencies", {}))

    async def save(self, path: Path):
        with open(path, "w") as fp:
            build_db_json = {
                "targets": self.targets,
                "dependencies": dict(self.dependencies),
            }
            json.dump(build_db_json, fp, indent=2)


@dataclass
class Builder:
    build: Coroutine[Target, None, None]
    add_source: Coroutine[Target, None, None]


class Handler:
    def can_handle(self, target: Target) -> bool:
        return False

    def stamp(self, target: Target) -> Stamp:
        return ""

    def stamps_match(self, a: Stamp, b: Stamp) -> bool:
        return a and b and a == b

    async def rebuild_impl(self, target: Target, builder: Builder):
        raise NotImplementedError(f"{self} cannot build {target!r}")


class FileHandler(Handler):
    def can_handle(self, target: Target) -> bool:
        return True

    def stamp(self, target: Target) -> Stamp:
        with contextlib.suppress(OSError):
            path = Path(target)
            if path.is_file():
                s = path.stat()
                # skipped: st_nlink, st_atime_ns because they don't indicate the file's changed
                # skipped: st_ino, st_dev because they can change as removable media is remounted
                return f"{s.st_mode} 0 0 {s.st_uid} {s.st_gid} {s.st_size} {s.st_mtime_ns} {s.st_ctime_ns}"

        return ""

    def stamps_match(self, a: str, b: str) -> bool:
        return a and b and a == b


@dataclass
class BuildSystem:
    db_path: Path
    handlers: list[Handler] = field(init=False, default_factory=list)
    db: BuildDB = field(init=False, default_factory=BuildDB)

    def get_handler(self, target: Target) -> Handler:
        target = str(target)
        for handler in self.handlers:
            if handler.can_handle(target):
                return handler
        return Handler()

    async def register_dependency(self, target: Target, dependency: Target):
        target = str(target)
        dependency = str(dependency)
        dep_handler = self.get_handler(dependency)
        self.db.dependencies[target][dependency] = dep_handler.stamp(dependency)

    async def rebuild(self, target: Target, level: int = 0):
        target = str(target)
        logger.info(f"{' '*2*level}rebuild({target=!r})")
        handler = self.get_handler(target)
        self.db.dependencies.pop(target, None)
        builder = Builder(
            partial(self.build_as_dependency, target, level=level + 1),
            partial(self.register_dependency, target),
        )
        await handler.rebuild_impl(target, builder)
        self.db.targets[target] = handler.stamp(target)
        await self.save_build_db()

    async def build_as_dependency(self, target: Target, dependency: Target, level: int = 0):
        target = str(target)
        dependency = str(dependency)
        await self.build(dependency, level)
        await self.register_dependency(target, dependency)

    async def build(self, target: Target, level: int = 0):
        target = str(target)
        logger.info(f"{' '*2*level}build({target=!r})")
        handler = self.get_handler(target)
        old_stamp = self.db.targets.get(target)
        cur_stamp = handler.stamp(target)
        if old_stamp is None or not handler.stamps_match(old_stamp, cur_stamp):
            await self.rebuild(target, level + 1)
            return
        elif old_stamp != cur_stamp:
            # upgrade weakly equal stamps to strongly equal ones
            self.db.targets[target] = cur_stamp

        for dep, old_dep_stamp in self.db.dependencies[target].items():
            if dep in self.db.targets:
                await self.build(dep, level + 1)
            dep_handler = self.get_handler(dep)
            cur_dep_stamp = dep_handler.stamp(dep)
            if not dep_handler.stamps_match(old_dep_stamp, cur_dep_stamp):
                await self.rebuild(target, level + 1)
                return
            elif old_dep_stamp != cur_dep_stamp:
                # upgrade weakly equal stamps to strongly equal ones
                self.db.dependencies[target][dep] = cur_dep_stamp

    async def load_build_db(self):
        await self.db.load(self.db_path)

    async def save_build_db(self):
        await self.db.save(self.db_path)
