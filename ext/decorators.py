from discord.ext import commands
from discord import DMChannel


def guild_available():
    def pred(ctx) -> bool:
        return True if isinstance(ctx.channel, DMChannel) else not ctx.guild.unavailable

    return commands.check(pred)


def is_me():
    def pred(ctx) -> bool:
        return ctx.author.id == 548803750634979340

    return commands.check(pred)
