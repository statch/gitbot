from typing import TypedDict


class LOCGitBotJSONEntry(TypedDict):
    ignore: str | list[str]


class ReleaseFeedGitBotJSONEntry(TypedDict):
    ignore: str


class GitbotRepoConfig(TypedDict, total=False):
    loc: LOCGitBotJSONEntry
    release_feed: ReleaseFeedGitBotJSONEntry
