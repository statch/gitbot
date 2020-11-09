import aiohttp
from discord.ext import commands, tasks
from os import getenv


class DiscordBotListStats(commands.Cog):
    def __init__(self, client):
        self.client: commands.Bot = client
        self.token: str = getenv("DISCORDBOTLIST")
        self.post_dblst_stats.start()

    @tasks.loop(minutes=30)
    async def post_dblst_stats(self) -> None:
        async with aiohttp.ClientSession() as session:
            async with session.post(f"https://discordbotlist.com/api/v1/bots/{self.client.user.id}/stats",
                                    json={"guilds": len(self.client.guilds),
                                          "users": int(sum([g.member_count for g in self.client.guilds]))},
                                    headers={"Content-Type": "application/json", "Authorization": self.token}) as res:
                if res.status != 200:
                    res = await res.json()
                    print(f"\ndiscordbotlist API error:\n\n{res}\n")
                else:
                    print("discordbotlist stats posted successfully")

    @post_dblst_stats.before_loop
    async def wait_until_ready(self) -> None:
        await self.client.wait_until_ready()


def setup(client):
    client.add_cog(DiscordBotListStats(client))
