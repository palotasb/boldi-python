import importlib.metadata
from typing import Generic, Iterable, NamedTuple, Type, TypeVar

T = TypeVar("T")


class Plugin(NamedTuple, Generic[T]):
    name: str
    cls: Type[T]


def load(group: str, *, subclass: Type[T] = type) -> Iterable[Plugin[T]]:
    entry_points = importlib.metadata.entry_points()
    for entry_point in entry_points:
        if entry_point.group == group:
            cls = entry_point.load()
            if isinstance(cls, type) and issubclass(cls, subclass):
                yield Plugin(entry_point.name, cls)
            else:
                raise TypeError(f"expected {entry_point} to be subclass of {subclass} but got {type(cls)}")
