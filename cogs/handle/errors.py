from discord.ext import commands
from bot import PRODUCTION
from core.globs import Mgr


class Errors(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error) -> None:
        if isinstance(error, commands.MissingRequiredArgument):
            await Mgr.error(ctx, ctx.l.errors.missing_required_argument)
        elif isinstance(error, commands.CommandOnCooldown):
            await Mgr.error(ctx, ctx.l.errors.command_on_cooldown.format('{:.2f}'.format(error.retry_after)))
        elif isinstance(error, commands.MaxConcurrencyReached):
            await Mgr.error(ctx, ctx.l.errors.max_concurrency_reached)
        elif isinstance(error, commands.BotMissingPermissions):
            await Mgr.error(ctx,
                ctx.l.errors.bot_missing_permissions.format(', '.join([f'`{m}`' for m in error.missing_perms]).replace('_', ' ')))
        elif isinstance(error, commands.MissingPermissions):
            await Mgr.error(ctx,
                ctx.l.errors.missing_permissions.format(', '.join([f'`{m}`' for m in error.missing_perms]).replace('_', ' ')))
        elif isinstance(error, commands.NoPrivateMessage):
            await Mgr.error(ctx, ctx.l.errors.no_private_message)
        elif not PRODUCTION:
            raise error
        else:
            print(error)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Errors(bot))
