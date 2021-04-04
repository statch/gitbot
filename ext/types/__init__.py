from typing import Union, Tuple, List
from ..structs import DictProxy, DirProxy

__all__: tuple = (
    'DictSequence',
    'AnyDict'
)

AnyDict = Union[dict, DictProxy]
DictSequence = Union[Tuple[AnyDict], List[AnyDict], DirProxy]
