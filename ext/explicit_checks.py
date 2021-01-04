import discord


async def verify_send_perms(channel: discord.TextChannel) -> bool:
    if isinstance(channel, discord.DMChannel):
        return True
    perms: list = list(iter(channel.permissions_for(channel.guild.me)))
    overwrites: list = list(iter(channel.overwrites_for(channel.guild.me)))
    checks: list = ["send_messages", "read_messages", "read_message_history"]
    reqs: list = [(req, True) for req in checks]
    if all(x in perms for x in reqs) or all(x in overwrites for x in reqs) or ("administrator", True) in perms:
        return True
    else:  # Can't send a message
        return False
