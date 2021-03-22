from typing import Any, Union


class JSONProxy(dict):
    def __init__(self, data: Union[dict, list]):
        if isinstance(data, dict):
            super().__init__(data)
            for k, v in data.items():
                setattr(self, k, v)
        else:
            self.__items: list = data

    def __iter__(self):
        yield from self.__items

    def __getitem__(self, item: Union[str, int]) -> Any:
        if hasattr(self, '__items'):
            return self.__items[item]
        return getattr(self, item)
