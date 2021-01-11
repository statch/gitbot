import aiohttp
from discord.ext import commands, tasks
from os import getenv


class DiscordExtremeListStats(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.token: str = getenv("DISCORDEXTREMELIST")
        self.post_del_stats.start()

    @tasks.loop(minutes=15)
    async def post_del_stats(self):
        async with aiohttp.ClientSession() as session:
            async with session.post(f"https://api.discordextremelist.xyz/v2/bot/{self.bot.user.id}/stats",
                                    json={"guildCount": len(self.bot.guilds)},
                                    headers={"Content-Type": "application/json", "Authorization": self.token}) as res:
                res_ = await res.json()
            if res.status != 200:
                print(f"\ndiscordextremelist API error:\n\n{res_}\n")
            else:
                print("discordextremelist stats posted successfully")

    @post_del_stats.before_loop
    async def wait_until_ready(self):
        await self.bot.wait_until_ready()


def setup(bot: commands.Bot) -> None:
    bot.add_cog(DiscordExtremeListStats(bot))
