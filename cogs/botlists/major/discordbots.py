import aiohttp
from discord.ext import commands, tasks
from os import getenv


class DiscordBotsStats(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot
        self.token: str = getenv("DISCORDBOTS")
        self.post_dbots_stats.start()

    @tasks.loop(minutes=15)
    async def post_dbots_stats(self):
        async with aiohttp.ClientSession() as session:
            async with session.post(f"https://discord.bots.gg/api/v1/bots/{self.bot.user.id}/stats",
                                    json={"guildCount": len(self.bot.guilds)},
                                    headers={"Content-Type": "application/json", "Authorization": self.token}) as res:
                res_ = await res.json()
            if res.status != 200:
                print(f"\ndiscord.bots API error:\n\n{res_}\n")
            else:
                print("discord.bots stats posted successfully")

    @post_dbots_stats.before_loop
    async def wait_until_ready(self):
        await self.bot.wait_until_ready()


def setup(bot: commands.Bot) -> None:
    bot.add_cog(DiscordBotsStats(bot))
