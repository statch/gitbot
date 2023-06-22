from discord.ext import commands
from lib.structs import GitBotEmbed, GitBot
from lib.utils.decorators import gitbot_command
from lib.structs.discord.context import GitBotContext


class License(commands.Cog):
    def __init__(self, bot: GitBot):
        self.bot: GitBot = bot

    @gitbot_command(name='license')
    @commands.cooldown(10, 20, commands.BucketType.user)
    async def license_command(self, ctx: GitBotContext, *, license_: str) -> None:
        license_: dict = self.bot.mgr.get_license(license_)
        if license_ is None:
            return await ctx.error(ctx.l.license.error)
        embed: GitBotEmbed = GitBotEmbed(
            color=self.bot.mgr.c.rounded,
            title=license_['name'],
            url=license_['html_url']
        )
        embed.add_field(name=ctx.l.license.description, value=f'```{license_["description"]}```')
        embed.add_field(name=ctx.l.license.implementation, value=f'```{license_["implementation"]}```')
        embed.add_field(name=ctx.l.license.permissions,
                        value=''.join([f'{self.bot.mgr.e.circle_green}  {x}\n' for x in license_['permissions']]) if len(
                              license_['permissions']) != 0 else ctx.l.license.none, inline=True)
        embed.add_field(name=ctx.l.license.conditions,
                        value=''.join([f'{self.bot.mgr.e.circle_yellow}  {x}\n' for x in license_['conditions']]) if len(
                             license_['conditions']) != 0 else ctx.l.license.none, inline=True)
        embed.add_field(name=ctx.l.license.limitations,
                        value=''.join([f'{self.bot.mgr.e.circle_red}  {x}\n' for x in license_['limitations']]) if len(
                             license_['limitations']) != 0 else ctx.l.license.none, inline=True)
        await ctx.send(embed=embed, view_on_url=license_['html_url'])


async def setup(bot: GitBot) -> None:
    await bot.add_cog(License(bot))
