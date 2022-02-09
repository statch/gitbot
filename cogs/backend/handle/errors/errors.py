from discord.ext import commands
from lib.globs import Mgr
from lib.structs.discord.context import GitBotContext
from .error_tools import respond_to_command_doesnt_exist, log_error_in_discord,  silenced  # noqa


class Errors(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx: GitBotContext, error) -> None:
        ctx.fmt.set_prefix('errors')
        if not Mgr.env.production and not getattr(ctx, '__autoinvoked__', False):
            raise error
        if silenced(ctx, error):
            return
        match error:
            case commands.MissingRequiredArgument:
                await ctx.error(ctx.l.errors.missing_required_argument)
            case commands.CommandOnCooldown:
                await ctx.error(ctx.fmt('command_on_cooldown', '{:.2f}'.format(error.retry_after)))
            case commands.MaxConcurrencyReached:
                await ctx.error(ctx.l.errors.max_concurrency_reached)
            case commands.BotMissingPermissions:
                await ctx.error(ctx.fmt('bot_missing_permissions',
                                      ', '.join([f'`{m}`' for m in error.missing_perms]).replace('_', ' ')))
            case commands.MissingPermissions:
                await ctx.error(ctx.fmt('missing_permissions',
                                      ', '.join([f'`{m}`' for m in error.missing_perms]).replace('_', ' ')))
            case commands.NoPrivateMessage:
                await ctx.error(ctx.l.errors.no_private_message)
            case commands.CommandNotFound:
                await respond_to_command_doesnt_exist(ctx, error)
                if Mgr.env.production:
                    await log_error_in_discord(ctx, error)
            case _:
                if not ctx.__autoinvoked__:
                    await log_error_in_discord(ctx, error)
                    print(error)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Errors(bot))
