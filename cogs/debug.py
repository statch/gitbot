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
        rate = await Git.get_ratelimit()
        await ctx.send(
            f"{self.emoji} Used **{rate['rate']['used']}** out of **{rate['rate']['limit']}** requests so far.\n\n**Resets at:** `{dt.datetime.fromtimestamp(rate['rate']['reset']).strftime('%Y-%m-%d %H:%M:%S')}`")


def setup(client):
    client.add_cog(Debug(client))
