from typing import Optional, Any
from ..dicts.max_age_dict import CaseInsensitiveMaxAgeDict
from ..dicts.fixed_size_ordered_dict import CaseInsensitiveFixedSizeOrderedDict

__all__: tuple = ('BaseCache',)


class BaseCache(CaseInsensitiveMaxAgeDict, CaseInsensitiveFixedSizeOrderedDict):
    """
    The base class that nearly all cache structures should inherit from.
    Operations on this special instance of :class:`dict` are case-insensitive.

    :param maxsize: The max number of keys to hold in the cache, delete the oldest one upon setting a new one if full
    :param max_age: The time to store cache keys for in seconds
    """

    def __init__(self, maxsize: int = 128, max_age: Optional[int] = None):
        CaseInsensitiveFixedSizeOrderedDict.__init__(self, maxsize=maxsize)
        CaseInsensitiveMaxAgeDict.__init__(self, max_age=max_age)

    def __setitem__(self, key: Any, value: Any) -> Any:
        CaseInsensitiveMaxAgeDict.__setitem__(self, key, value)
        return CaseInsensitiveFixedSizeOrderedDict._pop(self)

    def __getitem__(self, key: Any) -> Any:
        return CaseInsensitiveMaxAgeDict.__getitem__(self, key)
