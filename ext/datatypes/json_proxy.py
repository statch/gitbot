from typing import Any, Union


class JSONProxy(dict):
    def __init__(self, data: Union[dict, list]):
        if isinstance(data, dict):
            super().__init__(data)
            for k, v in data.items():
                setattr(self, k, (v if not isinstance(v, dict) else JSONProxy(v)))
        self.__items: list = data

    def __getattr__(self, item: str) -> Any:  # PyCharmo no bullo pleaso
        return getattr(self, item)

    def __iter__(self):
        yield from self.__items

    def __getitem__(self, item: Union[str, int]) -> Any:
        return self.__items[item]
