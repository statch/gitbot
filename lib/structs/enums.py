import enum


@enum.unique
class CheckFailureCode(enum.IntEnum):
    MISSING_RELEASE_FEED_CHANNEL_PERMISSIONS_GUILDWIDE = 0x01
    NO_GUILD_RELEASE_FEEDS = 0x02


@enum.unique
class GitBotCommandState(enum.Enum):
    FAILURE: int = 0
    CONTINUE: int = 1
    SUCCESS: int = 2
    TIMEOUT: int = 3
    CLOSED: int = 4
