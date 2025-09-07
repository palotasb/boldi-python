# import importlib.machinery
import importlib
import importlib.util
import os
import sys
from collections.abc import Sequence
from importlib.abc import MetaPathFinder
from itertools import product, starmap
from pathlib import Path


def init():
    sys.meta_path.insert(0, DottedModuleNameImporter())


def enable_shim(module_name):
    print(f"Enabling shim for {module_name}", file=sys.stderr)


class DottedModuleNameImporter(MetaPathFinder):
    def find_spec(self, fullname: str, path: Sequence[str] | None, target=None):
        # Implements PathEntryFinder.find_spec
        # https://docs.python.org/3/library/importlib.html#importlib.abc.PathEntryFinder.find_spec
        names = fullname.split(".")
        seps = tuple(product("/.", repeat=len(names)))
        seps = tuple(filter(lambda sep: "." in sep, seps))
        paths = [tuple(zip(names, sep)) for sep in seps]
        paths = [tuple(starmap(lambda x, y: x + y, p)) for p in paths]
        paths = tuple(map("".join, paths))

        for maybe_lib_folder in path or sys.path:
            maybe_lib_folder = maybe_lib_folder or os.getcwd()
            if Path(maybe_lib_folder).is_dir():
                for path in paths:
                    ext = "__init__.py" if path.endswith("/") else ".py"
                    full_path = Path(maybe_lib_folder) / f"{path}{ext}"
                    if full_path.exists() and full_path.is_file():
                        return importlib.util.spec_from_file_location(fullname, full_path)

        return None
