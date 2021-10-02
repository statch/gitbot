from discord.ext import commands
from lib.globs import Mgr
from .error_tools import respond_to_command_doesnt_exist, log_error_in_discord,  is_error_case  # noqa


class Errors(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error) -> None:
        setattr(ctx, 'fmt', Mgr.fmt(ctx))
        ctx.fmt.set_prefix('errors')
        if is_error_case(ctx, commands.MissingRequiredArgument, error):
            await ctx.err(ctx.l.errors.missing_required_argument)
        elif is_error_case(ctx, commands.CommandOnCooldown, error):
            await ctx.err(ctx.fmt('command_on_cooldown', '{:.2f}'.format(error.retry_after)))
        elif is_error_case(ctx, commands.MaxConcurrencyReached, error):
            await ctx.err(ctx.l.errors.max_concurrency_reached)
        elif is_error_case(ctx, commands.BotMissingPermissions, error):
            await ctx.err(ctx.fmt('bot_missing_permissions',
                                  ', '.join([f'`{m}`' for m in error.missing_perms]).replace('_', ' ')))
        elif is_error_case(ctx, commands.MissingPermissions, error):
            await ctx.err(ctx.fmt('missing_permissions',
                                  ', '.join([f'`{m}`' for m in error.missing_perms]).replace('_', ' ')))
        elif is_error_case(ctx, commands.NoPrivateMessage, error):
            await ctx.err(ctx.l.errors.no_private_message)
        elif is_error_case(ctx, commands.CommandNotFound, error):
            await respond_to_command_doesnt_exist(ctx, error)
            if Mgr.env.production:
                await log_error_in_discord(ctx, error)
        elif not Mgr.env.production and not ctx.__autoinvoked__:
            raise error
        else:
            if not ctx.__autoinvoked__:
                await log_error_in_discord(ctx, error)
                print(error)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Errors(bot))
