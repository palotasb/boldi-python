from typing import Generic, Iterable, NamedTuple, Type, TypeVar

import backports.entry_points_selectable

T = TypeVar("T")


class Plugin(NamedTuple, Generic[T]):
    name: str
    obj: Type[T]


def load(name: str, *, subclass: Type[T] = type, prefix="boldi.") -> Iterable[Plugin[T]]:
    entry_points = backports.entry_points_selectable.entry_points(group=f"{prefix}{name}")
    for entry_point in entry_points:
        obj = entry_point.load()
        if issubclass(obj, subclass):
            yield Plugin(entry_point.name, obj)
        else:
            raise TypeError(f"expected {entry_point} to be subclass of {subclass} but got {type(obj)}")
