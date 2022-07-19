import discord
import platform
import datetime
import os
import psutil
from discord.ext import commands
from lib.globs import Mgr
from os.path import isfile, isdir, join
from lib.utils.decorators import gitbot_command
from lib.structs.discord.context import GitBotContext
from lib.structs import GitBotEmbed


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


LINES_OF_CODE: int = sum((dir_line_count('./cogs'),
                          dir_line_count('./lib'),
                          dir_line_count('./resources'),
                          item_line_count('./bot.py')))


class BotInfo(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot

    @gitbot_command(name='uptime', aliases=['up'])
    @commands.cooldown(15, 30, commands.BucketType.member)
    async def uptime_command(self, ctx: GitBotContext) -> None:
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
            color=Mgr.c.rounded,
            title=None,
            description=f'{Mgr.e.timer}  {ctx.fmt("uptime", uptime_stamp)}'
        )
        await ctx.send(embed=embed)

    @gitbot_command(name='ping')
    @commands.cooldown(15, 30, commands.BucketType.member)
    async def ping_command(self, ctx: GitBotContext) -> None:
        embed: discord.Embed = discord.Embed(
            color=Mgr.c.rounded,
            description=f"{Mgr.e.timer}  {ctx.fmt('ping', round(self.bot.latency * 1000))}"
        )
        await ctx.send(embed=embed)

    @gitbot_command(name='legal', aliases=['policy', 'privacy', 'tos', 'terms', 'privacy-policy', 'terms-of-service'])
    @commands.cooldown(15, 30, commands.BucketType.member)
    async def privacy_policy(self, ctx: GitBotContext) -> None:
        embed: GitBotEmbed = GitBotEmbed.from_locale_resource(ctx, 'legal',
                                                              color=0x00afe8,
                                                              url='https://statch.org/gitbot/legal')
        embed.description += '\n```\nhttps://statch.org/gitbot/legal```'
        await embed.send(ctx)

    @gitbot_command(name='support')
    @commands.cooldown(15, 30, commands.BucketType.member)
    async def support_command(self, ctx: GitBotContext) -> None:
        embed: discord.Embed = discord.Embed(
            color=Mgr.c.rounded,
            description=ctx.l.support.description
        )
        embed.set_author(icon_url=self.bot.user.avatar_url, name=ctx.l.support.title)
        await ctx.send(embed=embed)

    @gitbot_command(name='invite')
    @commands.cooldown(15, 30, commands.BucketType.member)
    async def invite_command(self, ctx: GitBotContext) -> None:
        embed: discord.Embed = discord.Embed(
            color=Mgr.c.rounded,
            description=f'[**{ctx.l.invite.invite_verb} {self.bot.user.name}**](https://discord.com/oauth2/authorize?client_id'
                        f'=761269120691470357&scope=bot&permissions=67488832) | [**{ctx.l.invite.server}**]('
                        'https://discord.gg/3e5fwpA)'
        )
        embed.set_author(icon_url=self.bot.user.avatar_url, name=ctx.l.invite.tagline)
        await ctx.send(embed=embed)

    @gitbot_command(name='vote')
    @commands.cooldown(15, 30, commands.BucketType.member)
    async def vote_command(self, ctx: GitBotContext) -> None:
        embed: discord.Embed = discord.Embed(
            color=Mgr.c.rounded,
            description='[**top.gg**](https://top.gg/bot/761269120691470357/vote) | [**botsfordiscord.com**]('
                        'https://botsfordiscord.com/bot/761269120691470357)'
        )
        embed.set_author(name=ctx.l.vote, icon_url=self.bot.user.avatar_url)
        await ctx.send(embed=embed)

    @gitbot_command(name='stats')
    @commands.cooldown(15, 30, commands.BucketType.member)
    async def stats_command(self, ctx: GitBotContext) -> None:
        ctx.fmt.set_prefix('stats')
        embed: discord.Embed = discord.Embed(color=Mgr.c.rounded)
        users: int = sum([x.member_count for x in self.bot.guilds])
        memory: str = '**{:.3f}GB** RAM'.format(process.memory_info()[0] / 2. ** 30)  # memory use in GB... I think
        cpu: str = f'**{psutil.cpu_percent()}%** CPU,'
        embed.add_field(name=f"{Mgr.e.stats}  {ctx.lp.title}", value=ctx.lp.body,
                        inline=False)
        embed.add_field(name=ctx.lp.system, value=f"{cpu}\n{memory}")
        embed.add_field(name=ctx.lp.people.title,
                        value=ctx.fmt('stats people body', len(self.bot.guilds), users))
        embed.add_field(name=ctx.lp.code.title,
                        value=ctx.fmt('stats code body', LINES_OF_CODE, f'{platform.system()} {platform.release()}'))
        await ctx.send(embed=embed)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(BotInfo(bot))
