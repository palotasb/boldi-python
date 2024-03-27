from typing import Generic, Iterable, NamedTuple, Type, TypeVar

import importlib_metadata

T = TypeVar("T")


class Plugin(NamedTuple, Generic[T]):
    name: str
    cls: Type[T]


def load(group: str, *, subclass: Type[T] = type) -> Iterable[Plugin[T]]:
    entry_points = importlib_metadata.entry_points(group=group)
    for entry_point in entry_points:
        cls = entry_point.load()
        if isinstance(cls, type) and issubclass(cls, subclass):
            yield Plugin(entry_point.name, cls)
        else:
            raise TypeError(f"expected {entry_point} to be subclass of {subclass} but got {type(cls)}")
