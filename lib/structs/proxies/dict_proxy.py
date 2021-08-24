from typing import Any, Union, Optional, Iterator
from ..dicts.case_insensitive_dict import CaseInsensitiveDict


class DictProxy(CaseInsensitiveDict):
    """A wrapper around :class:`CaseInsensitiveDict` allowing dotted access.

    .. note::
        Allows :class:`list` as well for ease of use when dealing with JSON files.

    Parameters
    ----------
    data: :class:`Union[:class:`dict`, :class:`list`]`
        The object to wrap with DictProxy.
    """

    def __init__(self, data: Optional[Union[list, dict[str, Any]]] = None):
        if data is None:
            data: dict = {}
        self.__items: Union[list, dict] = data
        if isinstance(data, dict):
            super().__init__(data)
            for k, v in data.items():
                setattr(self, k.casefold(), (v if not isinstance(v, dict) else DictProxy(v)))
        else:
            self.__getitem__ = lambda i: self.__items[i]

    @property
    def actual(self) -> Union[dict[str, Any], list]:
        return self.__items

    def __iter__(self) -> Iterator[Any]:
        yield from self.__items

    def __getattr__(self, item: Union[str, int]) -> Any:
        return super().__getitem__(item)

    def __setattr__(self, key: str, value: Any) -> None:
        super().__setitem__(key, value if type(value) != 'dict' else DictProxy(value))
