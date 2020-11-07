from discord.ext import commands, tasks
from discord import Game, Activity, ActivityType
from random import randint


class Background(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.next: int = 0
        self.status_changer.start()

    @tasks.loop(minutes=randint(1, 3))
    async def status_changer(self):
        presences: list = [Game(f"on {len(self.client.guilds)} servers"),
                           Activity(type=ActivityType.watching, name="git --help"),
                           Game(
                               f"for {sum([x.member_count for x in self.client.guilds])} users!"),
                           Activity(
                               type=ActivityType.listening, name="your Git feed")]
        await self.client.change_presence(activity=presences[self.next])
        if self.next != len(presences) - 1:
            self.next += 1
        else:
            self.next: int = 0

    @status_changer.before_loop
    async def wait_for_ready(self):
        await self.client.wait_until_ready()


def setup(client):
    client.add_cog(Background(client))
