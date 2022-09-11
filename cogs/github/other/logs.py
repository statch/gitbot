import discord
from discord.ext import commands
from lib.utils.decorators import gitbot_command
from lib.structs import GitBotEmbed, GitBot
from lib.structs.discord.context import GitBotContext


class Logs(commands.Cog):
    def __init__(self, bot: GitBot):
        self.bot: GitBot = bot

    @gitbot_command(name='logs', aliases=['logging', 'log'])
    @commands.cooldown(3, 60, commands.BucketType.guild)
    @commands.bot_has_permissions(manage_webhooks=True)
    @commands.has_permissions(manage_webhooks=True)
    @commands.guild_only()
    async def logs_command(self, ctx: GitBotContext) -> None:
        ctx.fmt.set_prefix('logs')
        try:
            self.bot.mgr.debug(f'Creating webhook in channel with ID {ctx.channel.id}')
            webhook: discord.Webhook = await ctx.channel.create_webhook(name='GitHub Logs',
                                                                        reason=f'GitHub Logs setup by {ctx.author}')
        except (discord.errors.HTTPException, discord.errors.Forbidden):
            await ctx.error(ctx.l.logs.webhook_failed)
            return
        embed: GitBotEmbed = GitBotEmbed(
            color=0x4287f5,
            title=f'{self.bot.mgr.e.github}  Repo Logs',
            description=(ctx.l.logs.description
                         + '\n'
                         + '\n'.join([f'{self.bot.mgr.e.square} {instruction}' for instruction in ctx.l.logs.instructions])
                         + '\n' + ':warning: ' + ctx.l.logs.do_not_share_warning + ' :warning:'),
            footer=ctx.l.logs.footer
        )
        try:
            url_embed: discord.Embed = discord.Embed(
                color=0x4287f5,
                title=f'{self.bot.mgr.e.github} {ctx.l.logs.dm_title}',
                description=f'||{webhook.url + "/github"}||'
            )
            await ctx.author.send(embed=url_embed)
        except discord.errors.HTTPException:
            await ctx.error(ctx.l.logs.dm_failed)
            try:
                await webhook.delete(reason=f'GitHub Logs setup by {ctx.author} failed')
            except discord.errors.HTTPException:
                pass
            return
        await ctx.send(embed=embed)


async def setup(bot: GitBot) -> None:
    await bot.add_cog(Logs(bot))
