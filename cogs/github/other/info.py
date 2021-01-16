from discord.ext import commands
from core import bot_config
from ext.manager import Manager
from typing import Optional

Git = bot_config.Git
mgr = Manager()


class Info(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot
        self.e: str = "<:ge:767823523573923890>"
        self.d1: str = mgr.emojis["circle_green"]
        self.d2: str = mgr.emojis["circle_yellow"]
        self.d3: str = mgr.emojis["circle_red"]

    @commands.command(name='info')
    @commands.cooldown(10, 20, commands.BucketType.user)
    async def info_command_group(self, ctx: commands.Context, link: str):
        ref: Optional[tuple] = await mgr.get_link_reference(link)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Info(bot))
