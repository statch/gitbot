import topgg
from discord.ext import commands
from os import getenv


class TopGGStats(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot
        self.token: str = getenv("TOPGG")
        self.gg: topgg.DBLClient = topgg.DBLClient(bot, self.token, autopost=True)

    @commands.Cog.listener()
    async def on_autopost_success(self):
        print("Successfully posted stats to top.gg")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(TopGGStats(bot))
