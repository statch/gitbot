import discord
import secrets
import string
from time import time
from discord.ext import commands
from lib.structs import GitBot, GitBotEmbed, GitBotContext
from lib.utils.decorators import gitbot_hybrid_group


class Auth(commands.Cog):
    def __init__(self, bot: GitBot):
        self.bot: GitBot = bot

    @gitbot_hybrid_group(name='auth', aliases=['a'], invoke_without_command=True, enabled=False, hidden=True)
    async def auth(self, ctx: GitBotContext) -> None:
        await ctx.group_help()

    @auth.command(name='github', aliases=['gh'], description='Authorize with GitHub to access extended functionality', enabled=False, hidden=True)
    async def auth_github_command(self, ctx: GitBotContext) -> None | discord.Message:
        if not ctx.interaction and not isinstance(ctx.channel, discord.DMChannel):
            return await ctx.error(ctx.l.errors.use_in_private)
        ctx.fmt.set_prefix('auth github')
        embed: GitBotEmbed = GitBotEmbed(
                color=self.bot.mgr.c.brand_colors.neon_bloom,
                title=f'{self.bot.mgr.e.github}  {ctx.fmt("title")}',
                description=ctx.fmt('description')
        )
        view: discord.ui.View = discord.ui.View()
        secret: str = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(16))
        view.add_item(discord.ui.Button(label=ctx.fmt('button'),
                                        url=self.bot.mgr.build_github_oauth_url(ctx.author.id, secret),
                                        style=discord.ButtonStyle.link))
        await self.bot.db.users.update_one({'_id': ctx.author.id}, {'$set': {'github': {
            'pending': True,
            'secret': secret,
            'exp': int(time()) + self.bot.mgr.env.oauth.github.auth_timeout
        }}}, upsert=True)
        await ctx.send(embed=embed, view=view, ephemeral=True)


async def setup(bot: GitBot) -> None:
    await bot.add_cog(Auth(bot))
