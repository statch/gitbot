from discord.ext import commands
from os import getenv
import statcord


class Statcord(commands.Cog):
    def __init__(self, client):
        self.client: commands.Bot = client
        self.key: str = getenv('STATCORD')
        self.api: statcord.Client = statcord.Client(self.client, self.key)
        self.api.start_loop()

    @commands.Cog.listener()
    async def on_command(self, ctx):
        self.api.command_run(ctx)


def setup(client):
    client.add_cog(Statcord(client))
