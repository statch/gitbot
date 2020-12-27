from discord.ext import commands, tasks
from discord import Game, Activity, ActivityType
from random import randint
from itertools import cycle


class Background(commands.Cog):
    def __init__(self, client):
        self.client: commands.Bot = client
        self.next: int = 0
        self.status_changer.start()

    @tasks.loop(minutes=randint(2, 5))
    async def status_changer(self):
        presences: cycle = cycle([Game(f"in {len(self.client.guilds)} servers"),
                                  Activity(type=ActivityType.watching, name="git --help"),
                                  Game(
                                      f"for {sum([x.member_count for x in self.client.guilds])} users!"),
                                  Activity(
                                      type=ActivityType.listening, name="your Git feed")])
        await self.client.change_presence(activity=next(presences))

    @status_changer.before_loop
    async def wait_for_ready(self):
        await self.client.wait_until_ready()


def setup(client: commands.Bot) -> None:
    client.add_cog(Background(client))
