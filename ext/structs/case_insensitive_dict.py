from typing import Any


class CaseInsensitiveDict(dict):
    """
    A subclass of :class:`dict` borrowed from discord.py, allowing case-insensitive operations.
    Due to the casefold() calls, it only accepts :class:`str` as keys
    """

    def __contains__(self, key: str) -> bool:
        return super().__contains__(key.casefold())

    def __delitem__(self, key: str) -> None:
        return super().__delitem__(key.casefold())

    def __getitem__(self, key: str) -> Any:
        return super().__getitem__(key.casefold())

    def get(self, key: str, default: Any = None) -> Any:
        return super().get(key.casefold(), default)

    def pop(self, key: str, default: Any = None) -> Any:
        return super().pop(key.casefold(), default)

    def __setitem__(self, key: str, value: Any) -> None:
        super().__setitem__(key.casefold(), value)
