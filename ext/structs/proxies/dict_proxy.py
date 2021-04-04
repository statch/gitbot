from typing import Any, Union


class DictProxy(dict):
    """A wrapper around :class:`dict` (Allows :class:`list` for ease of use when dealing with JSON files) allowing dotted access.

    Parameters
    ----------
    data: :class:`Union[:class:`dict`, :class:`list`]`
        The object to wrap with DictProxy.
    """

    def __init__(self, data: Union[dict, list]):
        self.__items: Union[list, dict] = data
        if isinstance(data, dict):
            super().__init__(data)
            for k, v in data.items():
                setattr(self, k, (v if not isinstance(v, dict) else DictProxy(v)))

    def __iter__(self):
        yield from self.__items

    def __getitem__(self, item: Union[str, int]) -> Any:
        return self.__items[item]

    def __setitem__(self, key, value):
        setattr(self, key, DictProxy(value) if isinstance(value, dict) else value)
