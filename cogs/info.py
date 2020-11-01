from discord.ext import commands
from cfg import globals
from ext.decorators import guild_available
from ext.manager import Manager
from discord import Embed

Git = globals.Git
mgr = Manager()


class Info(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.e: str = "<:ge:767823523573923890>"
        self.d1: str = mgr.emojis["circle_green"]
        self.d2: str = mgr.emojis["circle_red"]

    @commands.group(name='info')
    @commands.cooldown(10, 20, commands.BucketType.user)
    @guild_available()
    async def info_command_group(self, ctx):
        if ctx.invoked_subcommand is None:
            return await ctx.send(
                f"{self.e} Looks like you're lost! **Use the command** `git --help` **to get back on track.**")

    @info_command_group.command(name='--license', aliases=['-L', '-l', 'L', 'l'])
    @commands.cooldown(10, 20, commands.BucketType.user)
    @guild_available()
    async def get_license(self, ctx, *, lcns: str) -> None:
        lcns: dict = mgr.correlate_license(lcns)
        if lcns is None:
            return await ctx.send(f"{self.e}  I couldn't find a license matching the name you provided!")
        embed = Embed(
            color=0xefefef,
            title=lcns["name"],
            url=lcns["html_url"],
            description=None
        )
        embed.add_field(name=f"Description", value=f'```{lcns["description"]}```', inline=False)
        embed.add_field(name="Implementation", value=f'```{lcns["implementation"]}```', inline=False)
        embed.add_field(name="Permissions", value="".join([f"{self.d1}  {x}\n" for x in lcns["permissions"]]) if len(
            lcns["permissions"]) != 0 else "None")
        embed.add_field(name="Conditions",
                        value="".join([f":white_small_square:  {x}\n" for x in lcns["conditions"]]) if len(
                            lcns["conditions"]) != 0 else "None")
        embed.add_field(name="Limitations", value="".join([f"{self.d2}  {x}\n" for x in lcns["limitations"]]) if len(
            lcns["limitations"]) != 0 else "None")
        await ctx.send(embed=embed)


def setup(client):
    client.add_cog(Info(client))
