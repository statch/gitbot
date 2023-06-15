import enum

__all__: tuple = ('CheckFailureCode', 'GitBotCommandState',)


@enum.unique
class CheckFailureCode(enum.IntEnum):
    MISSING_RELEASE_FEED_CHANNEL_PERMISSIONS_GUILDWIDE = 0x01
    NO_GUILD_RELEASE_FEEDS = 0x02


@enum.unique
class GitBotCommandState(enum.Enum):
    FAILURE: int = 0x01
    CONTINUE: int = 0x02
    SUCCESS: int = 0x03
    TIMEOUT: int = 0x04
    CLOSED: int = 0x05
