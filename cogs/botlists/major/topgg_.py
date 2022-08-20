import topgg
from discord.ext import commands
from os import getenv
from lib.structs import GitBot


class TopGGStats(commands.Cog):
    def __init__(self, bot: GitBot):
        self.bot: GitBot = bot
        self.token: str = getenv('TOPGG')
        self.gg: topgg.DBLClient = topgg.DBLClient(bot, self.token, autopost=True)

    @commands.Cog.listener()
    async def on_autopost_success(self):
        self.bot.logger.info('Successfully posted stats to top.gg')


async def setup(bot: GitBot) -> None:
    await bot.add_cog(TopGGStats(bot))
