from discord.ext import commands
from os import getenv
import dlabs


class DiscordLabsStats(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.token: str = getenv("DISCORDLABS")
        self.discord_labs = dlabs.Client(
            bot=self.bot, token=self.token, autopost=True, verbose=True
        )


def setup(bot: commands.Bot) -> None:
    bot.add_cog(DiscordLabsStats(bot))
