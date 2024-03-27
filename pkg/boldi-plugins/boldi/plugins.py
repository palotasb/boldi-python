from typing import Generic, Iterable, NamedTuple, Type, TypeVar

import importlib_metadata

T = TypeVar("T")


class Plugin(NamedTuple, Generic[T]):
    name: str
    cls: Type[T]


def load(group: str, *, cls: Type[T] = type) -> Iterable[Plugin[T]]:
    entry_points = importlib_metadata.entry_points(group=group)
    for entry_point in entry_points:
        plugin = entry_point.load()
        if isinstance(plugin, type) and issubclass(plugin, cls):
            yield Plugin(entry_point.name, plugin)
        else:
            raise TypeError(f"expected {entry_point} to be subclass of {cls} but got {type(cls)}")
