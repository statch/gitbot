from typing import Union, Optional, Iterator, ItemsView, TypeVar
from ..dicts.case_insensitive_dict import CaseInsensitiveDict


_KT = TypeVar('_KT', str, int, covariant=True)
_VT = TypeVar('_VT', str, int, bool, float, list, dict, covariant=True)


class DictProxy(CaseInsensitiveDict):
    """A wrapper around :class:`CaseInsensitiveDict` allowing dotted access.

    .. note::
        Allows :class:`list` as well for ease of use when dealing with JSON files.

    Parameters
    ----------
    data: :class:`Optional[:class:`Union[list[_VT]`, :class:`dict[_KT, _VT]`]]`
        The object to wrap with DictProxy.
    """

    def __init__(self, data: Optional[Union[list, dict[_KT, _VT]]] = None, **kwargs):
        if data is None:
            data: dict[_KT, _VT] = {}
        self.__items: Union[list[_VT], dict[_KT, _VT]] = data
        if isinstance(data, dict):
            data.update(kwargs)
            super().__init__(data)
            for k, v in data.items():
                setattr(self, k.casefold(), (v if not isinstance(v, dict) else DictProxy(v)))
        else:
            self.__getitem__ = lambda i: self.__items[i]

    @property
    def actual(self) -> Union[dict[_KT, _VT], list[_VT]]:
        return self.__items

    def items(self) -> ItemsView[_KT, _VT]:
        # We override this to exclude _dict_proxy__items from the ItemsView iterator
        yield from list(super().items())[1:]

    def __iter__(self) -> Iterator[_VT]:
        yield from self.__items

    def __getattr__(self, item: _KT) -> _VT:
        return super().__getitem__(item)

    def __setattr__(self, key: _KT, value: _VT) -> None:
        super().__setitem__(key, value if type(value) != 'dict' else DictProxy(value))
