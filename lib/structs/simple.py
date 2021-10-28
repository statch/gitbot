from recordclass import recordclass

__all__: tuple = (
    'GitCommandData',
    'GhProfileData',
    'ParsedRepositoryData'
)

GitCommandData = recordclass('GitCommandData', 'command kwargs')
GhProfileData = recordclass('GhProfileData', 'all_time month fortnight week day hour')
ParsedRepositoryData = recordclass('ParsedRepositoryData', 'owner name branch slashname')
