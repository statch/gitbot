import enum


@enum.unique
class CheckFailureCode(enum.IntEnum):
    MISSING_RELEASE_FEED_CHANNEL_PERMISSIONS_GUILDWIDE = 0x01
