from typing import Any, Union


class JSONProxy(dict):
    """A wrapper around :class:`dict` (And :class:`list` for ease of use) allowing dotted access.
    Mainly meant for use on dicts loaded from JSON files, but works on any type of :class:`dict`.

    Parameters
    ----------
    data: :class:`Union[:class:`dict`, :class:`list`]`
        The object to wrap with JSONProxy.
    """

    def __init__(self, data: Union[dict, list]):
        self.__items: Union[list, dict] = data
        if isinstance(data, dict):
            super().__init__(data)
            for k, v in data.items():
                setattr(self, k, (v if not isinstance(v, dict) else JSONProxy(v)))

    def __iter__(self):
        yield from self.__items

    def __getitem__(self, item: Union[str, int]) -> Any:
        return self.__items[item]
