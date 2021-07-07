import discord
from discord.ext import commands
from lib.globs import Mgr
from lib.utils.decorators import gitbot_command


class Commits(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot

    @gitbot_command(name='commits', aliases=['commit'])
    @commands.cooldown(3, 60, commands.BucketType.guild)
    @commands.bot_has_permissions(manage_webhooks=True)
    @commands.has_permissions(manage_webhooks=True)
    @commands.guild_only()
    async def commits_command(self, ctx: commands.Context) -> None:
        ctx.fmt.set_prefix('commits')
        try:
            webhook: discord.Webhook = await ctx.channel.create_webhook(name='GitHub Commits',
                                                                        reason=f'GitHub Commits setup by {ctx.author}')
        except discord.errors.HTTPException:
            await ctx.err(ctx.l.commits.webhook_failed)
            return
        embed: discord.Embed = discord.Embed(
            color=0x4287f5,
            title=f'{Mgr.e.github}  Commit Feed',
            description=(ctx.l.commits.description
                         + '\n'
                         + '\n'.join([f'{Mgr.e.square} {instruction}' for instruction in ctx.l.commits.instructions])
                         + '\n' + ':warning: ' + ctx.l.commits.do_not_share_warning + ' :warning:')
        )
        embed.set_footer(text=ctx.l.commits.footer)
        try:
            url_embed: discord.Embed = discord.Embed(
                color=0x4287f5,
                title=f'{Mgr.e.github} {ctx.l.commits.dm_title}',
                description=f'||{webhook.url + "/github"}||'
            )
            await ctx.author.send(embed=url_embed)
        except discord.errors.HTTPException:
            await ctx.err(ctx.l.commits.dm_failed)
            try:
                await webhook.delete(reason=f'GitHub Commits setup by {ctx.author} failed')
            except discord.errors.HTTPException:
                pass
            return
        await ctx.send(embed=embed)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Commits(bot))
