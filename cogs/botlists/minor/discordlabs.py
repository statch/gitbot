import dlabs
from discord.ext import commands
from os import getenv
from lib.structs import GitBot


class DiscordLabsStats(commands.Cog):
    def __init__(self, bot: GitBot):
        self.bot: GitBot = bot
        self.token: str = getenv('DISCORDLABS')
        self.discord_labs = dlabs.Client(bot=self.bot, token=self.token, autopost=True, verbose=True)


async def setup(bot: GitBot) -> None:
    await bot.add_cog(DiscordLabsStats(bot))
