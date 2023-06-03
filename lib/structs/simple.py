from recordclass import recordclass

__all__: tuple = (
    'GitCommandData',
    'ParsedRepositoryData'
)

GitCommandData = recordclass('GitCommandData', 'command kwargs')
ParsedRepositoryData = recordclass('ParsedRepositoryData', 'owner name branch slashname')
