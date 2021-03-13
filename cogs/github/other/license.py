from discord.ext import commands
from core.globs import Mgr
from discord import Embed


class License(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot
        self.e: str = "<:ge:767823523573923890>"
        self.d1: str = Mgr.emojis["circle_green"]
        self.d2: str = Mgr.emojis["circle_yellow"]
        self.d3: str = Mgr.emojis["circle_red"]

    @commands.command(name='--license', aliases=['license', '-license'])
    @commands.cooldown(10, 20, commands.BucketType.user)
    async def license_command(self, ctx: commands.Context, *, lcns: str) -> None:
        lcns: dict = Mgr.correlate_license(lcns)
        if lcns is None:
            await ctx.send(f"{self.e}  I couldn't find a license matching the name you provided!")
            return
        embed = Embed(
            color=0xefefef,
            title=lcns["name"],
            url=lcns["html_url"],
            description=None
        )
        embed.add_field(name=f"Description:",
                        value=f'```{lcns["description"]}```', inline=False)
        embed.add_field(name="Implementation:",
                        value=f'```{lcns["implementation"]}```', inline=False)
        embed.add_field(name="Permissions:", value="".join([f"{self.d1}  {x}\n" for x in lcns["permissions"]]) if len(
            lcns["permissions"]) != 0 else "None")
        embed.add_field(name="Conditions:",
                        value="".join([f"{self.d2}  {x}\n" for x in lcns["conditions"]]) if len(
                            lcns["conditions"]) != 0 else "None")
        embed.add_field(name="Limitations:", value="".join([f"{self.d3}  {x}\n" for x in lcns["limitations"]]) if len(
            lcns["limitations"]) != 0 else "None")
        await ctx.send(embed=embed)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(License(bot))
