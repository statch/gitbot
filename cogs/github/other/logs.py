import discord
from discord.ext import commands
from lib.globs import Mgr
from lib.utils.decorators import gitbot_command
from lib.structs import GitBotEmbed


class Logs(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot

    @gitbot_command(name='logs', aliases=['logging', 'log'])
    @commands.cooldown(3, 60, commands.BucketType.guild)
    @commands.bot_has_permissions(manage_webhooks=True)
    @commands.has_permissions(manage_webhooks=True)
    @commands.guild_only()
    async def logs_command(self, ctx: commands.Context) -> None:
        ctx.fmt.set_prefix('logs')
        try:
            Mgr.debug(f'Creating webhook in channel with ID {ctx.channel.id}')
            webhook: discord.Webhook = await ctx.channel.create_webhook(name='GitHub Logs',
                                                                        reason=f'GitHub Logs setup by {ctx.author}')
        except (discord.errors.HTTPException, discord.errors.Forbidden):
            await ctx.err(ctx.l.logs.webhook_failed)
            return
        embed: GitBotEmbed = GitBotEmbed(
            color=0x4287f5,
            title=f'{Mgr.e.github}  Repo Logs',
            description=(ctx.l.logs.description
                         + '\n'
                         + '\n'.join([f'{Mgr.e.square} {instruction}' for instruction in ctx.l.logs.instructions])
                         + '\n' + ':warning: ' + ctx.l.logs.do_not_share_warning + ' :warning:'),
            footer=ctx.l.logs.footer
        )
        try:
            url_embed: discord.Embed = discord.Embed(
                color=0x4287f5,
                title=f'{Mgr.e.github} {ctx.l.logs.dm_title}',
                description=f'||{webhook.url + "/github"}||'
            )
            await ctx.author.send(embed=url_embed)
        except discord.errors.HTTPException:
            await ctx.err(ctx.l.logs.dm_failed)
            try:
                await webhook.delete(reason=f'GitHub Logs setup by {ctx.author} failed')
            except discord.errors.HTTPException:
                pass
            return
        await ctx.send(embed=embed)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Logs(bot))
