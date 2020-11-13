import dbl
import discord
from discord.ext import commands
from os import getenv


class TopGG(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.token = getenv("TOPGG")
        self.dblpy = dbl.DBLClient(self.client, self.token, autopost=True)

    @commands.Cog.listener()
    async def on_dbl_vote(self, data):
        print(data)

    async def on_guild_post(self):
        print("---------------------\nStats Posted to Top.gg\n---------------------")


def setup(client):
    client.add_cog(TopGG(client))
