from typing import NewType

__all__: tuple = (
    'GitHubRepository',
    'GitHubUser',
    'GitHubOrganization',
    'GuildID',
    'TagName',
    'UserID',
    'PyPIProject',
    'Hash',
    'MessageAttachmentURL',
    'LocaleName',
    'NumericStr',
    'CratesIOCrate'
)


NumericStr = NewType('NumericStr', str)
GitHubRepository = NewType('GitHubRepository', str)
GitHubUser = NewType('GitHubUser', str)
GitHubOrganization = NewType('GitHubOrganization', str)
GuildID = NewType('GuildID', int)
TagName = NewType('TagName', str)
UserID = NewType('UserID', int)
PyPIProject = NewType('PyPIProject', str)
Hash = NewType('Hash', int)
MessageAttachmentURL = NewType('MessageAttachmentURL', str)
LocaleName = NewType('LocaleName', str)
CratesIOCrate = NewType('CratesIOProject', str)
