from recordclass import recordclass

__all__: tuple = (
    'GitCommandData',
    'ParsedRepositoryData',
    'DiscordPresenceData'
)

GitCommandData = recordclass('GitCommandData', 'command kwargs')
ParsedRepositoryData = recordclass('ParsedRepositoryData', 'owner name branch slashname')
DiscordPresenceData = recordclass('DiscordPresence', 'type name status')
