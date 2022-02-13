from typing import TypedDict, NamedTuple, Union, Literal, Optional
from lib.typehints.generic import TagName

__all__: tuple = (
    'ReleaseFeedRepo',
    'ReleaseFeedItem',
    'ReleaseFeed',
    'TagNameUpdateData',
    'ReleaseFeedItemMention'
)


ReleaseFeedItemMention = Union[int, Literal['everyone'], Literal['here']]


class ReleaseFeedRepo(TypedDict):
    """
    Represents a repo belonging to a :class:`ReleaseFeedItem`

    Attributes
    ----------
    name str: The name of the repo
    release str: The last recorded tag name of the repo's release
    """

    name: str
    tag: str


class ReleaseFeedItem(TypedDict, total=False):
    """
    Represents a release feed item from the database

    Attributes
    ----------
    cid int: The item's channel ID
    hook str: The webhook pointing to the channel
    repos list: The repos that belong to this ReleaseFeedItem
    """

    cid: int
    hook: str
    mention: Optional[ReleaseFeedItemMention]
    repos: list[ReleaseFeedRepo]


ReleaseFeed = list[ReleaseFeedItem]


class TagNameUpdateData(NamedTuple):
    """
    A collection that's used in batch-updating a GitBotGuild with new tag names

    Attributes
    ----------
    rfi ReleaseFeedItem: The RFI to which the RFR belongs
    rfr ReleaseFeedRepo: The RFR to update with the new TagName
    repos list: The new TagName replacing the old one
    """

    rfi: ReleaseFeedItem
    rfr: ReleaseFeedRepo
    tag: TagName
