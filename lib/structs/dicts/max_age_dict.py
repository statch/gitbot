from time import time
from typing import Optional, Any
from .case_insensitive_dict import CaseInsensitiveDict

__all__: tuple = ('MaxAgeDict', 'CaseInsensitiveMaxAgeDict')


class MaxAgeDict(dict):
    """
    A special subclass of :class:`dict` that allows setting a max age for keys.
    When accessing a saved key, a delete-hook is called first that checks if key age < max_age,
    if it's not, behaves like the key doesn't exist and deletes it.

    :param max_age: The max age for keys expressed in seconds
    """

    def __init__(self, max_age: Optional[int] = None):
        self.max_age: Optional[int] = max_age
        self._age_map: dict = {}
        super().__init__()

    def valid(self, key: Any, delete: bool = False) -> bool:
        if self.max_age is not None and (age := self.age(key)):
            if age < self.max_age:
                return True
            if delete:
                self.__delitem__(key)
            return False
        return True

    def get(self, key: Any, default: Any = None) -> Any:
        if self.valid(key, delete=True):
            return super().get(key, default)
        return default

    def age(self, key: Any, default: Any = 0) -> Any:
        if ts := self._age_map.get(key):
            return int(time()) - ts
        return default

    def __setitem__(self, key: Any, value: Any) -> None:
        self._age_map[key] = int(time())
        super().__setitem__(key, value)

    def __getitem__(self, key: Any) -> Any:
        if self.valid(key, delete=True):
            return super().__getitem__(key)
        raise KeyError

    def __delitem__(self, key: Any) -> None:
        del self._age_map[key]
        del self[key]


class CaseInsensitiveMaxAgeDict(CaseInsensitiveDict, MaxAgeDict):
    """
    A case-insensitive variant of :class:`MaxAgeDict`

    :param max_age: The max age for keys expressed in seconds
    """

    def __init__(self, max_age: Optional[int] = None):
        MaxAgeDict.__init__(self, max_age=max_age)
        CaseInsensitiveDict.__init__(self)

    def valid(self, key: Any, delete: bool = False) -> bool:
        return MaxAgeDict.valid(self, CaseInsensitiveDict._casefold(key), delete=delete)

    def age(self, key: Any, default: Any = None) -> Any:
        MaxAgeDict.age(self, CaseInsensitiveDict._casefold(key), default=default)

    def get(self, key: Any, default: Any = None) -> Any:
        return MaxAgeDict.get(self, CaseInsensitiveDict._casefold(key), default=default)

    def __getitem__(self, key: Any) -> Any:
        return MaxAgeDict.__getitem__(self, CaseInsensitiveDict._casefold(key))

    def __setitem__(self, key: Any, value: Any) -> None:
        MaxAgeDict.__setitem__(self, CaseInsensitiveDict._casefold(key), value)

    def __delitem__(self, key: Any) -> Any:
        MaxAgeDict.__delitem__(self, CaseInsensitiveDict._casefold(key))
