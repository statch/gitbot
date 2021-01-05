import discord

SEND_REQUIREMENTS: list = [("send_messages", True), ("read_messages", True), ("read_message_history", True)]


async def verify_send_perms(channel: discord.TextChannel) -> bool:
    if isinstance(channel, discord.DMChannel):
        return True
    perms: list = list(iter(channel.permissions_for(channel.guild.me)))
    overwrites: list = list(iter(channel.overwrites_for(channel.guild.me)))
    if all(req in perms + overwrites for req in SEND_REQUIREMENTS) or ("administrator", True) in perms:
        return True
    return False
