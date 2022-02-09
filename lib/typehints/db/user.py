from typing import TypedDict
from lib.typehints.generic import GitHubRepository, GitHubOrganization, GitHubUser, UserID, LocaleName

__all__: tuple = ('GitBotUser',)


class GitBotUser(TypedDict, total=False):
    _id: UserID
    user: GitHubUser
    locale: LocaleName
    repo: GitHubRepository
    org: GitHubOrganization
