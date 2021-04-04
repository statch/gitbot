from typing import Union, Tuple, List
from ..structs import JSONProxy, DirProxy

__all__: tuple = (
    'IterableDictSequence'
)

IterableDictSequence = Union[Tuple[Union[dict, JSONProxy]], List[Union[dict, JSONProxy]], DirProxy]
