import aiohttp
from discord.ext import commands, tasks
from os import getenv


class DiscordLabs(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.token: str = getenv("DISCORDLABS")
        self.post_dlabs_stats.start()

    @tasks.loop(minutes=30)
    async def post_dlabs_stats(self):
        async with aiohttp.ClientSession() as session:
            async with session.post(f"https://bots.discordlabs.org/v2/bot/{self.client.user.id}/stats",
                                    data={"token": self.token, "server_count": len(self.client.guilds)}) as res:
                res = await res.json()
                if str(res["error"]).lower() != "false":
                    print(f"\nbots.discordlabs API error:\n\n{res}\n")
                else:
                    print("bots.discordlabs stats posted successfully")

    @post_dlabs_stats.before_loop
    async def wait_until_ready(self):
        await self.client.wait_until_ready()


def setup(client):
    client.add_cog(DiscordLabs(client))
