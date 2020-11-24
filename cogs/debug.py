import discord.ext.commands as commands
from ext.decorators import is_me
from cfg import globals
import datetime as dt

Git = globals.Git


class Debug(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.emoji: str = '<:github:772040411954937876>'
        self.e: str = "<:ge:767823523573923890>"

    @is_me()
    @commands.command(name='dispatch', aliases=['--event', '--dispatch', 'event'])
    async def manually_trigger_event(self, ctx: commands.Context,  event: str):
        event = event.lower().replace('on_', "", 1)
        cor = {
            "guild_join": ctx.guild,
            "guild_remove": ctx.guild,
            "member_join": ctx.author,
            "member_remove": ctx.author
        }
        if (e := cor.get(event, None)) is not None:
            self.client.dispatch(event, e)
            await ctx.send(f"{self.emoji} Dispatched event `{event}`")
        else:
            await ctx.send(f"{self.e}  Failed to dispatch event `{event}`")

    @is_me()
    @commands.command(aliases=["--rate"])
    async def rate(self, ctx) -> None:
        rate = await Git.get_ratelimit()
        await ctx.send(
            f"{self.emoji} Used **{rate['rate']['used']}** out of **{rate['rate']['limit']}** requests so far.\n\n**Resets at:** `{dt.datetime.fromtimestamp(rate['rate']['reset']).strftime('%Y-%m-%d %H:%M:%S')}`")


def setup(client):
    client.add_cog(Debug(client))
