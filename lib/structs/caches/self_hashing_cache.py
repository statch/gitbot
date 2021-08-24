import hashlib
from lib.typehints import HashDigest
from typing import Any, Union, Optional
from ..caches.base_cache import BaseCache


__all__: tuple = ('SelfHashingCache',)


class SelfHashingCache(BaseCache):
    """
    A simple cache structure that automatically hashes keys.

    :param hashing_algorithm: The hashing algorithm to pass to hashlib.new()
    :param maxsize: The max number of keys to hold in the cache, delete the oldest one upon setting a new one if full
    :param max_age: The time to store cache keys for in seconds
    """

    def __init__(self, hashing_algorithm: str = 'sha256', maxsize: int = 128, max_age: Optional[int] = None):
        self.hashing_algorithm: str = hashing_algorithm
        super().__init__(maxsize=maxsize, max_age=max_age)

    def hash(self, value: str) -> bytes:
        return hashlib.new(self.hashing_algorithm, value.encode('utf8')).digest()

    def get(self, key: Union[str, HashDigest], default: Any = None) -> Any:
        ret: Any = super().get(key) or super().get(self.hash(key))
        if ret:
            return ret
        return default

    def __setitem__(self, key: str, value: Any):
        return super().__setitem__(self.hash(key), value)

    def __getitem__(self, key: Union[str, HashDigest]) -> Any:
        if ret := self.get(key):
            return ret
        raise KeyError(f'Key \'{key}\' (and its hash) doesn\'t exist in this cache')

    def __contains__(self, key: Union[str, HashDigest]) -> bool:
        return self.get(key) is not None
