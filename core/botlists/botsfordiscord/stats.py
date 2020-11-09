import aiohttp
from discord.ext import commands, tasks
from os import getenv


class BotsForDiscordStats(commands.Cog):
    def __init__(self, client):
        self.client: commands.Bot = client
        self.token: str = getenv("BOTSFORDISCORD")
        self.post_bfd_stats.start()

    @tasks.loop(minutes=30)
    async def post_bfd_stats(self) -> None:
        async with aiohttp.ClientSession() as session:
            async with session.post(f"https://botsfordiscord.com/api/bot/{self.client.user.id}",
                                    json={"server_count": len(self.client.guilds)},
                                    headers={"Content-Type": "application/json", "Authorization": self.token}) as res:
                if res.status != 200:
                    res = await res.json()
                    print(f"\nbotsfordiscord API error:\n\n{res}\n")
                else:
                    print("botsfordiscord stats posted successfully")

    @post_bfd_stats.before_loop
    async def wait_until_ready(self) -> None:
        await self.client.wait_until_ready()


def setup(client):
    client.add_cog(BotsForDiscordStats(client))
