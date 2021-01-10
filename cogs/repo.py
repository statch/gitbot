import discord
from discord.ext import commands


class Repo(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot


def setup(bot: commands.Bot):
    bot.add_cog(Repo(bot))
