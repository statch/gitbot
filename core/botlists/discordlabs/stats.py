from discord.ext import commands
from os import getenv
import dlabs


class DiscordLabsStats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.token: str = getenv("DISCORDLABS")
        self.discord_labs = dlabs.bot(bot=self.bot, token=self.token, autopost=True, verbose=True)


def setup(bot):
    bot.add_cog(DiscordLabsStats(bot))
