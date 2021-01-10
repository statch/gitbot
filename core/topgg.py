import dbl
import discord
from discord.ext import commands
from os import getenv


class TopGG(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.token = getenv("TOPGG")
        self.dblpy = dbl.DBLbot(self.bot, self.token, autopost=True)

    @commands.Cog.listener()
    async def on_guild_post(self):
        print("---------------------\nStats Posted to Top.gg\n---------------------")


def setup(bot):
    bot.add_cog(TopGG(bot))
