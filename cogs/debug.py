import discord.ext.commands as commands
from ext.decorators import is_me
from cfg import globals
import datetime as dt

Git = globals.Git


class Debug(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.emoji: str = '<:github:772040411954937876>'

    @is_me()
    @commands.command(aliases=["--rate"])
    async def rate(self, ctx) -> None:
        await ctx.send(
            f"{self.emoji} Used **{Git.user.rate_limiting[1] - Git.user.rate_limiting[0]}** out of **{Git.user.rate_limiting[1]}** requests so far.\n\n**Resets at:** `{dt.datetime.fromtimestamp(Git.user.rate_limiting_resettime).strftime('%Y-%m-%d %H:%M:%S')}`")


def setup(client):
    client.add_cog(Debug(client))
