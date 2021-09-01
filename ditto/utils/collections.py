import datetime
from collections import defaultdict

from collections.abc import Callable
from typing import Any, TypeVar


__all__ = (
    "summarise_list",
    "format_list",
    "LRUDict",
    "LRUDefaultDict",
    "TimedDict",
    "TimedLRUDict",
    "TimedLRUDefaultDict",
)


T = TypeVar("T")


def summarise_list(
    *list: T,
    func: Callable[[T], str] = str,
    max_items: int = 10,
    skip_first: bool = False,
) -> str:
    count = len(list)
    if count <= skip_first:
        return "None"

    max_items += skip_first
    info = ", ".join(func(item) for item in list[skip_first:max_items])
    if count > max_items:
        info += f" (+{count - max_items} More)"
    return info


def format_list(
    string: str, *list: Any, singular: str = "has", plural: str = "have", oxford_comma: bool = True
) -> str:
    if len(list) == 0:
        return string.format("no-one", singular)
    elif len(list) == 1:
        return string.format(list[0], singular)

    *rest, last = list
    rest_str = ", ".join(str(item) for item in rest)
    return string.format(rest_str + "," * oxford_comma + " and " + str(last), plural)


class TimedDict(dict):
    def __init__(self, expires_after: datetime.timedelta, *args, **kwargs):
        self.expires_after = expires_after
        self._state: dict[Any, datetime.datetime] = {}
        super().__init__(*args, **kwargs)

    def __cleanup(self):
        now = datetime.datetime.now(tz=datetime.timezone.utc)
        for key in list(super().keys()):
            try:
                delta = now - self._state[key]
                if delta > self.expires_after:
                    del self[key]
                    del self._state[key]
            except KeyError:
                pass

    def __contains__(self, key: Any) -> bool:
        self.__cleanup()
        return super().__contains__(key)

    def __setitem__(self, key: Any, value: Any):
        super().__setitem__(key, value)
        self._state[key] = datetime.datetime.now(tz=datetime.timezone.utc)

    def __getitem__(self, key: Any) -> Any:
        self.__cleanup()
        return super().__getitem__(key)


class LRUDict(dict):
    def __init__(self, max_size: int = 1024, *args, **kwargs):
        if max_size <= 0:
            raise ValueError("Maximum cache size must be greater than 0.")
        self.max_size = max_size
        super().__init__(*args, **kwargs)
        self.__cleanup()

    def __cleanup(self):
        while len(self) > self.max_size:
            del self[next(iter(self))]

    def __getitem__(self, key: Any) -> Any:
        value = super().__getitem__(key)
        self.__cleanup()
        return value

    def __setitem__(self, key: Any, value: Any):
        super().__setitem__(key, value)
        self.__cleanup()


class TimedLRUDict(LRUDict, TimedDict):
    def __init__(self, expires_after: datetime.timedelta, max_size: int = 1024, *args, **kwargs):
        super().__init__(max_size, expires_after, *args, **kwargs)


class LRUDefaultDict(LRUDict, defaultdict):
    def __init__(self, default_factory: Callable = None, max_size: int = 1024, *args, **kwargs):
        super().__init__(max_size, *args, **kwargs)
        self.default_factory = default_factory


class TimedLRUDefaultDict(LRUDict, TimedDict, defaultdict):
    def __init__(
        self, default_factory: Callable, expires_after: datetime.timedelta, max_size: int = 1024, *args, **kwargs
    ):
        super().__init__(max_size, expires_after, *args, **kwargs)
        self.default_factory = default_factory
