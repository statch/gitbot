from typing import Any


class CaseInsensitiveDict(dict):
    """
    A subclass of :class:`dict` borrowed from discord.py, allowing case-insensitive operations.
    Due to the casefold() calls, it only accepts :class:`str` as keys
    """

    def __contains__(self, k: str) -> bool:
        return super().__contains__(k.casefold())

    def __delitem__(self, k: str) -> None:
        return super().__delitem__(k.casefold())

    def __getitem__(self, k: str) -> Any:
        return super().__getitem__(k.casefold())

    def get(self, k: str, default: Any = None) -> Any:
        return super().get(k.casefold(), default)

    def pop(self, k: str, default: Any = None) -> Any:
        return super().pop(k.casefold(), default)

    def __setitem__(self, k: str, v: Any) -> None:
        super().__setitem__(k.casefold(), v)
