import discord
from discord.ext import commands
from lib.typehints.db.user import *
from lib.typehints.db.guild.guild import GitBotGuild
from lib.structs import DictProxy, DirProxy, CaseInsensitiveDict, MaxAgeDict, FixedSizeOrderedDict
from lib.typehints.db.guild.autoconv import AutomaticConversionSettings
from lib.typehints.generic import *
from lib.typehints.locale.help import *
from lib.typehints.resource_defs_wfallbacks import *
from lib.typehints.db.guild.release_feed import *
from lib.typehints.gitbot_config import *

__all__: tuple = (
    'DictSequence',
    'AnyDict',
    'Identity',
    'ReleaseFeedRepo',
    'ReleaseFeedItem',
    'ReleaseFeed',
    'GitHubRepository',
    'GuildID',
    'GitBotGuild',
    'TagName',
    'TagNameUpdateData',
    'GitHubUser',
    'GitHubOrganization',
    'PyPIProject',
    'AutomaticConversionSettings',
    'Hash',
    'MessageAttachmentURL',
    'EmbedLike',
    'GitBotUser',
    'LocaleName',
    'CommandHelp',
    'ArgumentExplainer',
    'CommandGroupHelp',
    'CratesIOCrate',
    'ReleaseFeedItemMention',
    'GitbotRepoConfig',
    'LocaleDictProxyDef',
    'GraphQLQueriesDirProxyDef'
)

AnyDict = dict | DictProxy | CaseInsensitiveDict | MaxAgeDict | FixedSizeOrderedDict
DictSequence = tuple[AnyDict] | list[AnyDict] | DirProxy
Identity = int | str | commands.Context
EmbedLike = discord.Embed | Type['lib.structs.discord.embed.GitBotEmbed']
