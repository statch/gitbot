from typing import Union, Tuple, List
from discord.ext import commands
from ..structs.case_insensitive_dict import CaseInsensitiveDict
from ..structs import DictProxy, DirProxy

__all__: tuple = (
    'DictSequence',
    'AnyDict',
    'Identifiable'
)

AnyDict = Union[dict, DictProxy, CaseInsensitiveDict]
DictSequence = Union[Tuple[AnyDict], List[AnyDict], DirProxy]
Identifiable = Union[commands.Context, int]
