import importlib.metadata
from collections.abc import Callable
from typing import Iterable, NamedTuple


class Plugin(NamedTuple):
    name: str
    impl: Callable[..., None]


def load(group: str) -> Iterable[Plugin]:
    entry_points = importlib.metadata.entry_points(group=group)
    for entry_point in entry_points:
        plugin = entry_point.load()
        yield Plugin(entry_point.name, plugin)
