# coding: utf-8

"""
Dot-access and case-insensitive proxy for dicts.
~~~~~~~~~~~~~~~~~~~
For ease of use when dealing with JSON files, it wraps lists as well.
:copyright: (c) 2020-present statch
:license: CC BY-NC-ND 4.0, see LICENSE for more details.
"""

from typing import TypeVar
from ..dicts.case_insensitive_dict import CaseInsensitiveDict, CaseInsensitiveSnakeCaseDict

_KT = TypeVar('_KT', str, int, covariant=True)
_VT = TypeVar('_VT', str, int, bool, float, list, dict, covariant=True)


class DictProxy(CaseInsensitiveDict):
    """A wrapper around :class:`CaseInsensitiveDict` allowing dotted access.

    Parameters
    ----------
    data: :class:`dict[_KT, _VT]` | None
        The object to wrap with DictProxy.
    """

    def __init__(self, data: dict[_KT, _VT] | None = None, **kwargs):
        data: dict[_KT, _VT] = data if data else {}
        if kwargs:
            data.update(kwargs)
        super().__init__(data if data else {})
        for k, v in data.items():
            setattr(self, k.casefold(), (v if not isinstance(v, dict) else self.__class__(v)))

    def __getattr__(self, item: _KT) -> _VT:
        return super().__getitem__(item)

    def __setattr__(self, key: _KT, value: _VT) -> None:
        super().__setitem__(key, value if type(value) != 'dict' else self.__class__(value))

    def __new__(cls, data: list[_VT] | dict[_KT, _VT] | None = None, **kwargs):
        if data is None:
            data: dict[_KT, _VT] = {}
        if isinstance(data, dict):
            data.update(kwargs)
            return super().__new__(cls, data)
        elif isinstance(data, list):
            return list(i if not isinstance(i, dict) else cls(i) for i in data)


class SnakeCaseDictProxy(DictProxy, CaseInsensitiveSnakeCaseDict):
    ...
