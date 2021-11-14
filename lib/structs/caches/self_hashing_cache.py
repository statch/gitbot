from lib.typehints import Hash
from typing import Any, Optional
from ..caches.base_cache import BaseCache


__all__: tuple = ('SelfHashingCache',)


class SelfHashingCache(BaseCache):
    """
    A simple cache structure that automatically hashes keys.

    :param maxsize: The max number of keys to hold in the cache, delete the oldest one upon setting a new one if full
    :param max_age: The time to store cache keys for in seconds
    """

    def __init__(self, maxsize: int = 128, max_age: Optional[int] = None):
        super().__init__(maxsize=maxsize, max_age=max_age)

    def get(self, key: str | Hash, default: Any = None) -> Any:
        ret: Any = super().get(key) or super().get(hash(key))
        return ret or default

    def __setitem__(self, key: str, value: Any):
        return super().__setitem__(hash(key), value)

    def __getitem__(self, key: str | Hash) -> Any:
        if ret := self.get(key):
            return ret
        raise KeyError(f'Key \'{key}\' (and its hash) doesn\'t exist in this cache')

    def __contains__(self, key: str | Hash) -> bool:
        return self.get(key) is not None
