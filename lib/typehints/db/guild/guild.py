from typing import TypedDict
from lib.typehints.generic import GuildID
from lib.typehints.db.guild.release_feed import ReleaseFeed
from .autoconv import AutomaticConversion

__all__: tuple = (
    'GitBotGuild'
)


class GitBotGuild(TypedDict, total=False):
    """
    Represents a guild retrieved from the database

    Attributes
    ----------
    _id int: The ID of the guild and the primary key of the document
    feed ReleaseFeed: A list of ReleaseFeedItem
    """

    _id: GuildID
    feed: ReleaseFeed
    autoconv: AutomaticConversion
