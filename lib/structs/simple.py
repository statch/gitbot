from collections import namedtuple

__all__: tuple = (
    'GitCommandData',
    'GhProfileData'
)

GitCommandData = namedtuple('GitCommandData', 'command kwargs')
GhProfileData = namedtuple('GhProfileData', 'all_time month fortnight week day hour')
