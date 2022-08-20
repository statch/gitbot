from os import getenv
from lib.structs import GitBot
from discord.ext import commands, tasks


class TopCordStats(commands.Cog):
    def __init__(self, bot: GitBot):
        self.bot: GitBot = bot
        self.token: str = getenv('TOPCORD')
        self.post_topcord_stats.start()

    @tasks.loop(minutes=15)
    async def post_topcord_stats(self):
        async with self.bot.session.post(f'https://topcord.xyz/api/bot/stats/{self.bot.user.id}',
                                         json={'guilds': len(self.bot.guilds), 'shards': 0},
                                         headers={'Content-Type': 'application/json', 'Authorization': self.token}) as res:
            res_ = await res.json()
        if res.status != 200:
            self.bot.logger.error(f'\ntopcord API error:\n\n{res_}\n')
        else:
            self.bot.logger.info('Topcord stats posted successfully')

    @post_topcord_stats.before_loop
    async def wait_until_ready(self):
        await self.bot.wait_until_ready()


async def setup(bot: GitBot) -> None:
    await bot.add_cog(TopCordStats(bot))
