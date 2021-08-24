from typing import Union
from discord.ext import commands
from lib.structs.dicts.case_insensitive_dict import CaseInsensitiveDict
from lib.structs import DictProxy, DirProxy
from lib.typehints.db.guild.guild import GitBotGuild
from lib.typehints.db.guild.release_feed import ReleaseFeedRepo, ReleaseFeedItem, ReleaseFeed, TagNameUpdateData
from lib.typehints.db.guild.autoconv import AutomaticConversion
from lib.typehints.generic import (Repository, GuildID,
                                   TagName, GitHubUser,
                                   Organization, PyPIProject,
                                   HashDigest, MessageAttachmentURL)

__all__: tuple = (
    'DictSequence',
    'AnyDict',
    'Identity',
    'ReleaseFeedRepo',
    'ReleaseFeedItem',
    'ReleaseFeed',
    'Repository',
    'GuildID',
    'GitBotGuild',
    'TagName',
    'TagNameUpdateData',
    'GitHubUser',
    'Organization',
    'PyPIProject',
    'AutomaticConversion',
    'HashDigest',
    'MessageAttachmentURL'
)

AnyDict = Union[dict, DictProxy, CaseInsensitiveDict]
DictSequence = Union[tuple[AnyDict], list[AnyDict], DirProxy]
Identity = Union[int, str, commands.Context]
