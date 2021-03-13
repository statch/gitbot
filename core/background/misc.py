import os
from itertools import cycle
from random import randint

import discord
import statcord
from discord.ext import commands, tasks

from bot import PRODUCTION


class MiscellaneousBackgroundTasks(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot
        self.status_changer.start()
        if PRODUCTION:
            self.statcord: statcord.Client = statcord.Client(
                self.bot, os.getenv("STATCORD")
            )
            self.statcord.start_loop()

    @tasks.loop(minutes=randint(2, 5))
    async def status_changer(self):
        presences: cycle = cycle(
            [
                discord.Game(f"in {len(self.bot.guilds)} servers"),
                discord.Activity(type=discord.ActivityType.watching, name="git --help"),
                discord.Activity(
                    type=discord.ActivityType.listening, name="your Git feed"
                ),
            ]
        )
        await self.bot.change_presence(activity=next(presences))

    @status_changer.before_loop
    async def wait_for_ready(self):
        await self.bot.wait_until_ready()

    @commands.Cog.listener()
    async def on_command(self, ctx: commands.Context):
        if PRODUCTION:
            self.statcord.command_run(ctx)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(MiscellaneousBackgroundTasks(bot))
