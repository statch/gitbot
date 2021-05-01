from typing import Any, Union, Optional, List, Dict


class DictProxy(dict):
    """A wrapper around :class:`dict` allowing dotted access.

    .. note::
        Allows :class:`list` as well for ease of use when dealing with JSON files.

    Parameters
    ----------
    data: :class:`Union[:class:`dict`, :class:`list`]`
        The object to wrap with DictProxy.
    """

    def __init__(self, data: Optional[Union[List[Union[list, str, int]], Dict[str, Union[list, str, int]]]] = None):
        if data is None:
            data: dict = {}
        self.__items: Union[list, dict] = data
        if isinstance(data, dict):
            super().__init__(data)
            for k, v in data.items():
                setattr(self, k, (v if not isinstance(v, dict) else DictProxy(v)))
        else:
            self.__getitem__ = lambda i: self.__items[i]

    def __iter__(self):
        yield from self.__items

    def __getattr__(self, item: Union[str, int]) -> Any:
        return self[item]
