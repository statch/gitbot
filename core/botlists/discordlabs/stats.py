from discord.ext import commands
from os import getenv
import dlabs


class DiscordLabsStats(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.token: str = getenv("DISCORDLABS")
        self.discord_labs = dlabs.Client(bot=self.client, token=self.token, autopost=True, verbose=True)


def setup(client):
    client.add_cog(DiscordLabsStats(client))
