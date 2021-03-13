import dbl
from discord.ext import commands
from os import getenv


class TopGG(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.token: str = getenv("TOPGG")
        self.dblpy: dbl.DBLClient = dbl.DBLClient(
            self.bot, self.token, autopost=True)

    @commands.Cog.listener()
    async def on_guild_post(self):
        print("---------------------\nStats Posted to Top.gg\n---------------------")


def setup(bot: commands.Bot) -> None:
    bot.add_cog(TopGG(bot))
