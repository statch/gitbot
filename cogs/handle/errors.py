from discord.ext import commands
from bot import PRODUCTION


class Errors(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot
        self.e: str = "<:ge:767823523573923890>"

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error) -> None:
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"{self.e}  You didn't pass in all of the arguments, **use** `git --help` **for info.**")
        elif isinstance(error, commands.CommandOnCooldown):
            msg = self.e + " " + '**You\'re on cooldown!** Please try again in {:.2f}s'.format(error.retry_after)
            await ctx.send(msg)
        elif isinstance(error, commands.MaxConcurrencyReached):
            await ctx.send(
                f"{self.e}  This command is experiencing exceptional traffic. **Please try again in a few seconds.**")
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send(
                f"{self.e}  **I am missing permissions required to do this!**"
                f" I need {', '.join([f'`{m}`' for m in error.missing_perms]).replace('_', ' ')}")
        elif not PRODUCTION:
            raise error
        else:
            print(error)


def setup(bot):
    bot.add_cog(Errors(bot))
