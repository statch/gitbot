from discord.ext import commands
from bot import PRODUCTION
from core.globs import Mgr


class Errors(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error) -> None:
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"{Mgr.e.err}  You didn't pass in all of the arguments, **use** `git --help` **for info.**")
        elif isinstance(error, commands.CommandOnCooldown):
            msg = Mgr.e.err + " " + '**You\'re on cooldown!** Please try again in {:.2f}s'.format(error.retry_after)
            await ctx.send(msg)
        elif isinstance(error, commands.MaxConcurrencyReached):
            await ctx.send(
                f"{Mgr.e.err}  This command is experiencing exceptional traffic. **Please try again in a few seconds.**")
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send(
                f"{Mgr.e.err}  **I am missing permissions required to do this!**"
                f" I need {', '.join([f'`{m}`' for m in error.missing_perms]).replace('_', ' ')}")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send(
                f"{Mgr.e.err}  **You're missing permissions required to do this!**"
                f" You need {', '.join([f'`{m}`' for m in error.missing_perms]).replace('_', ' ')}")
        elif isinstance(error, commands.NoPrivateMessage):
            await ctx.send(f'{Mgr.e.err}  This command can only be used **inside a server!**')
        elif not PRODUCTION:
            raise error
        else:
            print(error)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Errors(bot))
