from typing import Any, NoReturn, Optional, Literal
from ..caches.base_cache import BaseCache

__all__: tuple = (
    'TypedCache',
    'CacheSchema',
    'CacheValidationError',
    'CacheSchemaLikeType'
)


class CacheValidationError(Exception):
    """
    Informative error message when an action's types don't match the schema ones.
    """

    pass


class CacheSchema:
    """
    Schema structure to validate __setitem__ for :class:`TypedCache`

    :param key: The type of the keys to accept
    :param value: The type of the values to accept
    """

    def __init__(self, key: type | tuple[type, ...], value: type | tuple[type, ...]):
        self.key: type | tuple[type, ...] = key
        self.value: type | tuple[type, ...] = value

    def _raise(self,
               got: Any,
               expected: type | tuple[type, ...],
               /,
               value_name: Literal['cache key', 'cache value']) -> NoReturn:
        """
        Raise :class:`CacheValidationError` when the action's types don't match the schema ones.

        :param got: The argument that was received
        :param expected: The argument expected (self.key/value)
        :param value_name: The name of the value (cache key, cache value)
        :raise CacheValidationError: When the action's types don't match the schema ones
        """

        raise CacheValidationError(f'Expected type \'{expected.__name__}\' for {value_name},'
                                   f' got: \'{got.__class__.__name__}\' ({repr(got)})')

    def __call__(self, key: Any, value: Any) -> None:
        if not isinstance(key, self.key):
            self._raise(key, self.key, 'cache key')
        elif not isinstance(value, self.value):
            self._raise(value, self.value, 'cache value')


CacheSchemaLikeType = CacheSchema | tuple[type | tuple[type, ...] | type | tuple[type, ...]]


class TypedCache(BaseCache):
    """
    A simple cache structure that validates __setitem__ actions with a predefined :class:`CacheSchema`.

    :param schema: The schema to use for validation
    :param maxsize: The max number of keys to hold in the cache, delete the oldest one upon setting a new one if full
    :param max_age: The time to store cache keys for in seconds
    """

    def __init__(self, schema: CacheSchemaLikeType, maxsize: int = 128, max_age: Optional[int] = None):
        self.schema: CacheSchema = schema if isinstance(schema, CacheSchema) else CacheSchema(*schema)
        super().__init__(maxsize=maxsize, max_age=max_age)

    def __setitem__(self, key: Any, value: Any) -> None:
        self.schema(key, value)
        super().__setitem__(key, value)
