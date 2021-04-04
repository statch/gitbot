from typing import Union, Tuple, List
from ..structs import DictProxy, DirProxy

__all__: tuple = (
    'DictSequence'
)

DictSequence = Union[Tuple[Union[dict, DictProxy]], List[Union[dict, DictProxy]], DirProxy]
