from typing import Any


class CaseInsensitiveDict(dict):
    """
    A subclass of :class:`dict` borrowed from discord.py, allowing case-insensitive operations.
    """

    def _casefold(self, key: Any) -> Any:
        if hasattr(key, 'casefold'):
            return key.casefold()
        return key

    def __contains__(self, key: Any) -> bool:
        return super().__contains__(self._casefold(key))

    def __delitem__(self, key: Any) -> None:
        return super().__delitem__(self._casefold(key))

    def __getitem__(self, key: Any) -> Any:
        return super().__getitem__(self._casefold(key))

    def get(self, key: Any, default: Any = None) -> Any:
        return super().get(self._casefold(key), default)

    def pop(self, key: Any, default: Any = None) -> Any:
        return super().pop(self._casefold(key), default)

    def __setitem__(self, key: Any, value: Any) -> None:
        super().__setitem__(self._casefold(key), value)
