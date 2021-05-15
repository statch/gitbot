from discord.ext import commands
from bot import PRODUCTION
from globs import Mgr


class Errors(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error) -> None:
        setattr(ctx, 'fmt', Mgr.fmt(ctx))
        ctx.fmt.set_prefix('errors')
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.err(ctx.l.errors.missing_required_argument)
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.err(ctx.fmt('command_on_cooldown', '{:.2f}'.format(error.retry_after)))
        elif isinstance(error, commands.MaxConcurrencyReached):
            await ctx.err(ctx.l.errors.max_concurrency_reached)
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.err(ctx.fmt('bot_missing_permissions', ', '.join([f'`{m}`' for m in error.missing_perms]).replace('_', ' ')))
        elif isinstance(error, commands.MissingPermissions):
            await ctx.err(ctx.fmt('missing_permissions', ', '.join([f'`{m}`' for m in error.missing_perms]).replace('_', ' ')))
        elif isinstance(error, commands.NoPrivateMessage):
            await ctx.err(ctx.l.errors.no_private_message)
        elif not PRODUCTION:
            raise error
        else:
            print(error)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Errors(bot))
