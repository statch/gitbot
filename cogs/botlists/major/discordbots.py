from discord.ext import commands, tasks
from os import getenv
from lib.structs import GitBot


class DiscordBotsStats(commands.Cog):
    def __init__(self, bot: GitBot):
        self.bot: GitBot = bot
        self.token: str = getenv('DISCORDBOTS')
        self.post_dbots_stats.start()

    @tasks.loop(minutes=15)
    async def post_dbots_stats(self):
        async with self.bot.session.post(f'https://discord.bots.gg/api/v1/bots/{self.bot.user.id}/stats',
                                         json={'guildCount': len(self.bot.guilds)},
                                         headers={'Content-Type': 'application/json', 'Authorization': self.token}) as res:
            res_ = await res.json()
        if res.status != 200:
            self.bot.logger.error('discord.bots API error: %s', res_['error'])
        else:
            self.bot.logger.info('discord.bots stats posted successfully')

    @post_dbots_stats.before_loop
    async def wait_until_ready(self):
        await self.bot.wait_until_ready()


async def setup(bot: GitBot) -> None:
    await bot.add_cog(DiscordBotsStats(bot))
