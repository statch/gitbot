import discord
import statcord
from discord.ext import commands, tasks
from random import randint
from itertools import cycle
from lib.structs import GitBot, DiscordPresenceData
from lib.structs.discord.context import GitBotContext


class MiscellaneousBackgroundTasks(commands.Cog):
    presences: list
    presences_cycle: cycle

    def __init__(self, bot: GitBot):
        self.bot: GitBot = bot
        self.status_changer.start()
        self.raw_presences = self.bot.mgr.load_json('presences')
        self.make_presences()
        if self.bot.mgr.env.production:
            self.statcord: statcord.Client = statcord.Client(self.bot, self.bot.mgr.env.statcord)
            self.statcord.start_loop()

    def make_presences(self):
        self.presences: list = []
        for rp in self.raw_presences:
            self.presences.append(
                DiscordPresenceData(
                    name=rp.activity.name,
                    type=getattr(discord.ActivityType, rp.activity.type),
                    status=getattr(discord.Status, rp.status),
                )
            )
        self.presences_cycle: cycle = cycle(self.presences)
        # start the cycle at a random index
        for _ in range(randint(0, len(self.presences))):
            next(self.presences_cycle)
        self.bot.logger.info(f'Loaded {len(self.presences)} presences.')

    @tasks.loop(seconds=20)
    async def status_changer(self):
        presence: DiscordPresenceData = next(self.presences_cycle)
        await self.bot.change_presence(activity=discord.Activity(type=presence.type, name=presence.name), status=presence.status)

    @status_changer.before_loop
    async def wait_for_ready(self):
        await self.bot.wait_until_ready()

    @commands.Cog.listener()
    async def on_command(self, ctx: GitBotContext):
        if self.bot.mgr.env.production:
            self.statcord.command_run(ctx)


async def setup(bot: GitBot) -> None:
    await bot.add_cog(MiscellaneousBackgroundTasks(bot))
