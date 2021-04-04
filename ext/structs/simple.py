from collections import namedtuple

__all__: tuple = (
    'GitCommandData',
    'GhProfileData'
)

GitCommandData = namedtuple('GitCommandData', 'data type args')
GhProfileData = namedtuple('GhProfileData', 'all_time month fortnight week day hour')
