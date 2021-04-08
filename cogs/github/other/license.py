from discord.ext import commands
from core.globs import Mgr
from discord import Embed


class License(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot

    @commands.command(name='--license', aliases=['license', '-license'])
    @commands.cooldown(10, 20, commands.BucketType.user)
    async def license_command(self, ctx: commands.Context, *, license_: str) -> None:
        license_: dict = Mgr.correlate_license(license_)
        if license_ is None:
            await ctx.err(ctx.l.license.error)
            return
        embed = Embed(
            color=0xefefef,
            title=license_["name"],
            url=license_["html_url"]
        )
        embed.add_field(name=ctx.l.license.description, value=f'```{license_["description"]}```', inline=False)
        embed.add_field(name=ctx.l.license.implementation, value=f'```{license_["implementation"]}```', inline=False)
        embed.add_field(name=ctx.l.license.permissions,
                        value="".join([f"{Mgr.e.circle_green}  {x}\n" for x in license_["permissions"]]) if len(
                              license_["permissions"]) != 0 else ctx.l.license.none)
        embed.add_field(name=ctx.l.license.conditions,
                        value="".join([f"{Mgr.e.circle_yellow}  {x}\n" for x in license_["conditions"]]) if len(
                             license_["conditions"]) != 0 else ctx.l.license.none)
        embed.add_field(name=ctx.l.license.limitations,
                        value="".join([f"{Mgr.e.circle_red}  {x}\n" for x in license_["limitations"]]) if len(
                             license_["limitations"]) != 0 else ctx.l.license.none)
        await ctx.send(embed=embed)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(License(bot))
