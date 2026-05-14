import importlib.machinery
import importlib.metadata
import importlib.util
import os
import sys
from collections.abc import Sequence
from importlib.abc import MetaPathFinder
from pathlib import Path

ENTRY_POINT_GROUP = "boldi.dotmodpath"
FINDER: "DottedModuleNameFinder | None" = None


def install() -> "DottedModuleNameFinder":
    """Install the importer and register prefixes advertised by entry points."""
    global FINDER

    if FINDER is None:
        FINDER = DottedModuleNameFinder()
        try:
            path_finder_index = sys.meta_path.index(importlib.machinery.PathFinder)
            sys.meta_path.insert(path_finder_index + 1, FINDER)
        except ValueError:
            sys.meta_path.append(FINDER)

    # Entry point names are the import prefixes that may use dotted filenames.
    for entry_point in importlib.metadata.entry_points(group=ENTRY_POINT_GROUP):
        FINDER.register_prefix(entry_point.name)

    return FINDER


def mark_as_package(module_name: str) -> None:
    """Mark a dotted-file module as package-like so it can have submodules."""
    module = sys.modules[module_name]
    module_file = getattr(module, "__file__", None)
    if module_file is None:
        raise ValueError(f"{module_name!r} has no __file__")

    # A dotted-file module can opt into having submodules by setting __path__.
    module.__path__ = [str(Path(module_file).parent)]
    if module.__spec__:
        module.__spec__.submodule_search_locations = module.__path__


class DottedModuleNameFinder(MetaPathFinder):
    def __init__(self) -> None:
        self.prefixes: set[str] = set()

    def register_prefix(self, prefix: str) -> None:
        self.prefixes.add(prefix)

    def find_spec(self, fullname: str, path: Sequence[str] | None = None, target=None):
        for prefix in sorted(self.prefixes, key=len, reverse=True):
            if fullname != prefix and not fullname.startswith(f"{prefix}."):
                continue

            # For prefix "boldi.dotmodpath", search under the "boldi" package
            # for files named like "dotmodpath.foo.py".
            anchor = prefix.rpartition(".")[0]
            tail = fullname[len(anchor) + 1 :] if anchor else fullname
            module_file = f"{tail}.py"

            for root in self._roots(path, anchor):
                file = root / module_file
                if file.is_file():
                    return importlib.util.spec_from_file_location(fullname, file)

        return None

    @staticmethod
    def _roots(path: Sequence[str] | None, anchor: str) -> tuple[Path, ...]:
        if path is not None:
            # Submodule imports search inside the parent package's __path__.
            return tuple(root for entry in path if (root := Path(entry or os.getcwd())).is_dir())

        # Prefix imports search for the prefix anchor on sys.path.
        anchor_path = Path(*anchor.split(".")) if anchor else Path()
        return tuple(root for entry in sys.path if (root := Path(entry or os.getcwd()) / anchor_path).is_dir())
