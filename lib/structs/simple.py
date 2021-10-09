from collections import namedtuple

__all__: tuple = (
    'GitCommandData',
    'GhProfileData',
    'ParsedRepositoryData'
)

GitCommandData = namedtuple('GitCommandData', 'command kwargs')
GhProfileData = namedtuple('GhProfileData', 'all_time month fortnight week day hour')
ParsedRepositoryData = namedtuple('ParsedRepositoryData', 'owner name branch slashname')
