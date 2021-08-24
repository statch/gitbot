from collections import OrderedDict
from typing import Any
from ..dicts.case_insensitive_dict import CaseInsensitiveDict

__all__: tuple = ('FixedSizeOrderedDict', 'CaseInsensitiveFixedSizeOrderedDict')


class FixedSizeOrderedDict(OrderedDict):
    """
    A subclass of :class:`OrderedDict` that acts like a deque, useful for cache structures.
    """

    def __init__(self, maxsize: int = 128, **kwargs):
        self.maxsize: int = maxsize
        super().__init__(**kwargs)

    @property
    def full(self) -> bool:
        return len(self) == self.maxsize

    @property
    def first(self) -> Any:
        return next(iter(self), None)

    def _pop(self) -> Any:
        if len(self) > self.maxsize:
            return self.popitem(last=False)

    def __setitem__(self, key: Any, value: Any) -> Any:
        super().__setitem__(key, value)
        return self._pop()


class CaseInsensitiveFixedSizeOrderedDict(FixedSizeOrderedDict, CaseInsensitiveDict):
    """
    A case-insensitive variant of :class:`FixedSizeOrderedDict`
    """

    def __init__(self, maxsize: int = 128):
        FixedSizeOrderedDict.__init__(self, maxsize=maxsize)
        CaseInsensitiveDict.__init__(self)

    def __setitem__(self, key: Any, value: Any) -> Any:
        CaseInsensitiveDict.__setitem__(self, key, value)
        return self._pop()
