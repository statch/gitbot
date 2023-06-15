from typing import Any


class CaseInsensitiveDict(dict):
    """
    A subclass of :class:`dict` borrowed from discord.py, allowing case-insensitive operations.
    """

    @staticmethod
    def _casefold(key: Any) -> Any:
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

    def __repr__(self):
        return f'{self.__class__.__name__}({super().__repr__()})'


class CaseInsensitiveSnakeCaseDict(CaseInsensitiveDict):
    """
    A subclass of :class:`CaseInsensitiveDict` allowing snake_case operations.
    """

    def __init__(self, mapping: dict = None, **kwargs):
        if mapping is not None:
            mapping = {self._casefold(k): v for k, v in mapping.items()}
        super().__init__(mapping, **kwargs)

    def _casefold(self, key: Any) -> Any:
        return super()._casefold(''.join(['_' + let.lower() if let.isupper() and key[i-1] != '_' else let for i, let in enumerate(key)]).lstrip('_'))
