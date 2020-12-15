import discord.ext.commands as commands
import discord
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
    async def manually_trigger_event(self, ctx: commands.Context, event: str):
        event = event.lower().replace('on_', "", 1)
        cor = {
            "guild_join": ctx.guild,
            "guild_remove": ctx.guild,
            "member_join": ctx.author,
            "member_remove": ctx.author
        }
        if cor.get(event, None) is not None:
            e = cor.get(event, None)
            self.client.dispatch(event, e)
            await ctx.send(f"{self.emoji} Dispatched event `{event}`")
        else:
            await ctx.send(f"{self.e}  Failed to dispatch event `{event}`")

    @is_me()
    @commands.command(aliases=["--rate", "--ratelimit"])
    async def rate(self, ctx) -> None:
        rate = await Git.get_ratelimit()
        embed = discord.Embed(
            color=0xefefef,
            title=f"{self.e}  Rate-limiting",
            description=None
        )
        graphql = rate['resources']['graphql']
        rest = rate['rate']
        search = rate['resources']['search']
        embed.add_field(name="REST",
                        value=f"{rest['used']}/{rate['rate']['limit']}\n\
                        `{dt.datetime.fromtimestamp(rest['reset']).strftime('%X')}`")
        embed.add_field(name='GraphQL',
                        value=f"{graphql['used']}/{graphql['limit']}\n\
                        `{dt.datetime.fromtimestamp(graphql['reset']).strftime('%X')}`")
        embed.add_field(name='Search',
                        value=f"{search['used']}/{search['limit']}\n\
                        `{dt.datetime.fromtimestamp(search['reset']).strftime('%X')}`")
        await ctx.send(embed=embed)


def setup(client):
    client.add_cog(Debug(client))
