from typing import Any, Union


class DictProxy(dict):
    """A wrapper around :class:`dict` allowing dotted access.

    .. note::
        Allows :class:`list` as well for ease of use when dealing with JSON files.

    Parameters
    ----------
    data: :class:`Union[:class:`dict`, :class:`list`]`
        The object to wrap with DictProxy.
    """

    def __init__(self, data: Union[dict, list]):
        self.__items: Union[list, dict] = data
        if isinstance(data, dict):
            super().__init__({k: v if not isinstance(v, dict) else DictProxy(v) for k, v in data.items()})

    __getattr__ = dict.__getitem__
    __delattr__ = dict.__delitem__

    def __iter__(self):
        yield from self.__items

    def __getitem__(self, item: Union[str, int]) -> Any:
        return self.__items[item]

    def __setitem__(self, key: str, value: Any) -> None:
        setattr(self, key, DictProxy(value) if isinstance(value, dict) else value)
