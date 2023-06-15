from typing import TypedDict
from lib.typehints.generic import GitHubRepository, GitHubOrganization, GitHubUser, UserID, LocaleName

__all__: tuple = ('GitBotUser', 'GitBotUserGitHubCredentials')


class GitBotUserGitHubCredentials(TypedDict, total=False):
    pending: bool
    access_token: str
    scope: str


class GitBotUser(TypedDict, total=False):
    _id: UserID
    locale: LocaleName | str
    user: GitHubUser | str | None
    repo: GitHubRepository | str | None
    org: GitHubOrganization | str | None
    github: GitBotUserGitHubCredentials | None
