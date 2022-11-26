import enum


@enum.unique
class CheckFailureCode(enum.IntEnum):
    MISSING_RELEASE_FEED_CHANNEL_PERMISSIONS_GUILDWIDE = 0x01
    NO_GUILD_RELEASE_FEEDS = 0x02
