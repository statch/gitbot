from discord.ext import commands, tasks
from os import getenv
from lib.structs import GitBot


class DiscordBotListStats(commands.Cog):
    def __init__(self, bot: GitBot):
        self.bot: GitBot = bot
        self.token: str = getenv('DISCORDBOTLIST')
        self.post_dblst_stats.start()

    @tasks.loop(minutes=30)
    async def post_dblst_stats(self) -> None:
        async with self.bot.session.post(f'https://discordbotlist.com/api/v1/bots/{self.bot.user.id}/stats',
                                         json={'guilds': len(self.bot.guilds),
                                               'users': int(sum([g.member_count for g in self.bot.guilds]))},
                                         headers={'Content-Type': 'application/json', 'Authorization': self.token}) as res:
            if res.status != 200:
                res = await res.json()
                self.bot.logger.error('Discord Bot List API error: %s', str(res))
            else:
                self.bot.logger.info('Discord Bot List stats posted successfully')

    @post_dblst_stats.before_loop
    async def wait_until_ready(self) -> None:
        await self.bot.wait_until_ready()


async def setup(bot: GitBot) -> None:
    await bot.add_cog(DiscordBotListStats(bot))
