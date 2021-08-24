from typing import NewType

__all__: tuple = (
    'Repository',
    'GuildID',
    'TagName',
    'GitHubUser',
    'Organization',
    'UserID',
    'PyPIProject',
    'HashDigest',
    'MessageAttachmentURL'
)

Repository = NewType('Repository', str)
GitHubUser = NewType('GitHubUser', str)
Organization = NewType('Organization', str)
GuildID = NewType('GuildID', int)
TagName = NewType('TagName', str)
UserID = NewType('UserID', int)
PyPIProject = NewType('PyPIProject', str)
HashDigest = NewType('HashDigest', bytes)
MessageAttachmentURL = NewType('MessageAttachmentURL', str)
