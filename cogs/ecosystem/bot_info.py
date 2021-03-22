import discord
import platform
import datetime
import os
import psutil
from discord.ext import commands
from core.globs import Mgr
from os.path import isfile, isdir, join


pid: int = os.getpid()
process: psutil.Process = psutil.Process(pid)
start_time: datetime.datetime = datetime.datetime.utcnow()


def item_line_count(path) -> int:
    if isdir(path):
        return dir_line_count(path)
    elif isfile(path):
        return len(open(path, 'rb').readlines())
    return 0


def dir_line_count(directory) -> int:
    return sum(map(lambda item: item_line_count(join(directory, item)), os.listdir(directory)))


LINES_OF_CODE: int = sum([dir_line_count('./cogs'),
                          dir_line_count('./ext'),
                          dir_line_count('./core')])


class BotInfo(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot

    @commands.command(name='uptime', aliases=['--uptime', '-uptime', 'up', '--up', '-up'])
    @commands.cooldown(15, 30, commands.BucketType.member)
    async def uptime_command(self, ctx: commands.Context) -> None:
        now: datetime.datetime = datetime.datetime.utcnow()
        delta: datetime.timedelta = now - start_time
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        days, hours = divmod(hours, 24)
        if days:
            time_format: str = '**{d}** days, **{h}** hours, **{m}** minutes, and **{s}** seconds.'
        else:
            time_format: str = '**{h}** hours, **{m}** minutes, and **{s}** seconds.'
        uptime_stamp: str = time_format.format(d=days, h=hours, m=minutes, s=seconds)
        embed: discord.Embed = discord.Embed(
            color=0xefefef,
            title=None,
            description=f'{Mgr.e.timer}  **I have been online for:**\n{uptime_stamp}'
        )
        await ctx.send(embed=embed)

    @commands.command(name='ping', aliases=['--ping', '-ping'])
    @commands.cooldown(15, 30, commands.BucketType.member)
    async def ping_command(self, ctx: commands.Context) -> None:
        embed: discord.Embed = discord.Embed(
            color=0xefefef,
            description=f"{Mgr.e.timer}  **My ping is:**\n**{round(self.bot.latency * 1000)}** milliseconds"
        )
        await ctx.send(embed=embed)

    @commands.command(name='privacy', aliases=["policy", '--privacy', '-privacy', '-policy', '--policy'])
    @commands.cooldown(15, 30, commands.BucketType.member)
    async def privacy_policy(self, ctx: commands.Context) -> None:
        embed: discord.Embed = discord.Embed(
            color=0xefefef,
            title=f'{Mgr.e.github}  Privacy Policy'
        )
        embed.add_field(name="What is stored?", inline=False,
                        value="The only data stored are your User ID and quick access users, repos and orgs.")
        embed.add_field(name="How is all this used anyway?", inline=False,
                        value="It's used to provide storage for your saved users, repos and organizations, your User "
                              "ID is essential for the Bot to know, what data is yours.")
        embed.add_field(name="Who has access to this data?", inline=False,
                        value="Only the Bot's developer has access, no one else. Your data isn't viewed or accessed "
                              "in any way unless it's required to provide the service.")
        embed.add_field(name="How can I get rid of this stored data?", inline=False,
                        value="You can do that very easily by using the `git config -delete` command!")
        embed.add_field(name="Who wrote this and can this be changed?", inline=False,
                        value="This privacy policy was written by [wulf](https://dsc.bio/wulf), the Bot's developer, "
                              "and yes, all of this is subject to change in the future.")
        await ctx.send(embed=embed)

    @commands.command(name='invite', aliases=['--invite', '-invite'])
    @commands.cooldown(15, 30, commands.BucketType.member)
    async def invite_command(self, ctx: commands.Context) -> None:
        embed: discord.Embed = discord.Embed(
            color=0xefefef,
            description=f"[**Invite {self.bot.user.name}**](https://discord.com/oauth2/authorize?client_id"
                        f"=761269120691470357&scope=bot&permissions=67488832) | [**Support Server**]("
                        f"https://discord.gg/3e5fwpA) "
        )
        embed.set_author(icon_url=self.bot.user.avatar_url, name='Invite me to your server!')
        await ctx.send(embed=embed)

    @commands.command(name='vote', aliases=['--vote', '-vote'])
    @commands.cooldown(15, 30, commands.BucketType.member)
    async def vote_command(self, ctx: commands.Context) -> None:
        embed: discord.Embed = discord.Embed(
            color=0xefefef,
            description="[**top.gg**](https://top.gg/bot/761269120691470357/vote) | [**botsfordiscord.com**]("
                        "https://botsfordiscord.com/bot/761269120691470357) "
        )
        embed.set_author(name=f'Vote for {self.bot.user.name}!', icon_url=self.bot.user.avatar_url)
        await ctx.send(embed=embed)

    @commands.command(name='stats', aliases=['--stats', '-stats'])
    @commands.cooldown(15, 30, commands.BucketType.member)
    async def stats_command(self, ctx: commands.Context) -> None:
        embed: discord.Embed = discord.Embed(color=0xefefef)
        users: int = sum([x.member_count for x in self.bot.guilds])
        memory: str = "**{:.3f}GB** of RAM".format(process.memory_info()[0] / 2. ** 30)  # memory use in GB... I think
        cpu: str = f"**{psutil.cpu_percent()}%** CPU, and"
        embed.add_field(name=f"{Mgr.e.stats}  Bot Stats", value=f"General stats regarding the Bot's functioning.",
                        inline=False)
        embed.add_field(name="System Usage", value=f"{cpu}\n{memory}")
        embed.add_field(name="People",
                        value=f"I'm in **{len(self.bot.guilds)}** servers,\nand have **{users}** users")
        embed.add_field(name="Code",
                        value=f"I am **{LINES_OF_CODE}** lines of code,\nrunning on **{platform.system()} {platform.release()}**")
        await ctx.send(embed=embed)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(BotInfo(bot))
