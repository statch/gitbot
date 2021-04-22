import discord
from core.globs import Mgr
from discord.ext import commands


class Help(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot

    @commands.group(name='--help', aliases=['help', '-H'])
    @commands.cooldown(15, 30, commands.BucketType.user)
    async def help_command(self, ctx: commands.Context) -> None:
        if ctx.invoked_subcommand is None:
            lines: list = [ctx.l.help.default.description,
                           f"`git help github` {ctx.l.help.default.sections.github}",
                           f"`git help info` {ctx.l.help.default.sections.info}",
                           f"`git help config` {ctx.l.help.default.sections.config}",
                           f"`git help utility` {ctx.l.help.default.sections.utility}",
                           f"\n{ctx.l.help.default.support_server_note}"]
            embed = discord.Embed(
                title=f"{Mgr.e.err}  {ctx.l.help.default.title}",
                color=0xefefef,
                description="\n".join(lines)
            )
            embed.set_footer(text=ctx.l.help.default.footer)
            await ctx.send(embed=embed)

    @help_command.command(name='github', aliases=['-github', '--github'])
    @commands.cooldown(15, 30, commands.BucketType.user)
    async def github_help(self, ctx: commands.Context) -> None:
        lines: list = [ctx.l.help.github.description,
                       f"`git user -info {{{ctx.l.help.arguments.user}}}` - {ctx.l.help.github.commands.user.info}",
                       f"`git user -repos {{{ctx.l.help.arguments.user}}}` - {ctx.l.help.github.commands.user.repos}",
                       f"`git gist {{{ctx.l.help.arguments.user}}}` - {ctx.l.help.github.commands.gist}",
                       f"`git org -info {{{ctx.l.help.arguments.org}}}` - {ctx.l.help.github.commands.org.info}",
                       f"`git org -repos {{{ctx.l.help.arguments.org}}}` - {ctx.l.help.github.commands.org.repos}",
                       f"\n{ctx.l.help.github.commands.repo_argument_note}",
                       f"\n`git issue {{{ctx.l.help.arguments.repo}}} {{{ctx.l.help.arguments.issue_number}}}` - {ctx.l.help.github.commands.issue}",
                       f"`git pr {{{ctx.l.help.arguments.repo}}} {{{ctx.l.help.arguments.pr_number}}}` - {ctx.l.help.github.commands.pr}",
                       f"`git repo -info {{{ctx.l.help.arguments.repo}}}` - {ctx.l.help.github.commands.repo.info}",
                       f"`git repo -files {{{ctx.l.help.arguments.repo}}}` - {ctx.l.help.github.commands.repo.files}",
                       f"`git repo -issues {{{ctx.l.help.arguments.repo}}} ({ctx.l.help.arguments.state})` - {ctx.l.help.github.commands.repo.issues}",
                       f"`git repo -pulls {{{ctx.l.help.arguments.repo}}} ({ctx.l.help.arguments.state})` - {ctx.l.help.github.commands.repo.pulls}"]

        embed = discord.Embed(
            title=f"{Mgr.e.err}  {ctx.l.help.github.title}",
            color=0xefefef,
            description="\n".join(lines)
        )
        embed.set_footer(text=ctx.l.help.alias_note)
        await ctx.send(embed=embed)

    @help_command.command(name='utility', aliases=['-utility', '--utility'])
    @commands.cooldown(15, 30, commands.BucketType.user)
    async def utlity_help(self, ctx: commands.Context) -> None:
        lines: list = [ctx.l.help.utility.description,
                       f"`git license {{{ctx.l.help.arguments.license}}}` - {ctx.l.help.utility.commands.license}",
                       f"`git lines {{{ctx.l.help.arguments.link}}}` - {ctx.l.help.utility.commands.lines}",
                       f"`git info {{{ctx.l.help.arguments.link}}}` - {ctx.l.help.utility.commands.info}"]
        embed = discord.Embed(
            title=f"{Mgr.e.err}  {ctx.l.help.utility.title}",
            color=0xefefef,
            description="\n".join(lines)
        )
        embed.set_footer(text=ctx.l.help.alias_note)
        await ctx.send(embed=embed)

    @help_command.command(name='config', aliases=['-config', '--config'])
    @commands.cooldown(15, 30, commands.BucketType.user)
    async def config_help(self, ctx: commands.Context) -> None:
        lines: list = [ctx.l.help.config.description,
                       f"`git config` - {ctx.l.help.config.commands.default}",
                       f"`git config -show` - {ctx.l.help.config.commands.show}"]
        embed = discord.Embed(
            title=f"{Mgr.e.err}  {ctx.l.help.config.title}",
            color=0xefefef,
            description="\n".join(lines)
        )
        embed.set_footer(text=ctx.l.help.alias_note)
        await ctx.send(embed=embed)

    @help_command.command(name="info", aliases=["-info", "--info"])
    @commands.cooldown(15, 30, commands.BucketType.user)
    async def info_help(self, ctx: commands.Context) -> None:
        lines: list = [ctx.l.help.info.description,
                       f"`git aliases` - {ctx.l.help.info.commands.aliases}",
                       f"`git privacy` - {ctx.l.help.info.commands.privacy}",
                       f"`git vote` - {ctx.l.help.info.commands.vote}",
                       f"`git stats` - {ctx.l.help.info.commands.stats}",
                       f"`git uptime` - {ctx.l.help.info.commands.uptime}",
                       f"`git ping` - {ctx.l.help.info.commands.ping}"]

        embed = discord.Embed(
            title=f"{Mgr.e.err}  {ctx.l.help.info.title}",
            color=0xefefef,
            description="\n".join(lines)
        )
        embed.set_footer(text=ctx.l.help.alias_note)
        await ctx.send(embed=embed)

    @commands.group(name='--aliases', aliases=['aliases'])
    @commands.cooldown(15, 30, commands.BucketType.user)
    async def alias_command(self, ctx: commands.Context) -> None:
        if ctx.invoked_subcommand is None:
            lines: list = ["In this section you'll find shorthands of my commands",
                           "\n**You can access specific parts by typing:**",
                           "`git aliases github` - for GitHub command aliases",
                           "`git aliases info` - for other aliases",
                           "`git aliases config` - for configuration command aliases",
                           "`git aliases utility` - for utility command aliases"]
            embed = discord.Embed(
                title=f"{Mgr.e.err}  Aliases",
                color=0xefefef,
                description="\n".join(lines)
            )
            embed.set_footer(text=f"You can find usage of these commands by typing git --help")
            await ctx.send(embed=embed)

    @alias_command.command(name="github", aliases=['-github', '--github'])
    @commands.cooldown(15, 30, commands.BucketType.user)
    async def github_aliases(self, ctx: commands.Context) -> None:
        lines: list = ["Some commands default to their `info` variant if it's omitted:",
                       f"`git user -info` {Mgr.e.arrow} `git user`",
                       f"`git repo -info` {Mgr.e.arrow} `git repo`",
                       f"`git org -info` {Mgr.e.arrow} `git org`",
                       f"There are generic aliases as well:",
                       f"`git user -repos` {Mgr.e.arrow} `git user -r`",
                       f"`git org -repos` {Mgr.e.arrow} `git org -r`",
                       f"`git issue` {Mgr.e.arrow} `git i`"]
        embed = discord.Embed(
            title=f"{Mgr.e.err}  GitHub Aliases",
            color=0xefefef,
            description="\n".join(lines)
        )
        embed.set_footer(text=f"You can find usage of these commands by typing git --help github")
        await ctx.send(embed=embed)

    @alias_command.command(name="utility", aliases=['-utility', '--utility'])
    @commands.cooldown(15, 30, commands.BucketType.user)
    async def utility_aliases(self, ctx: commands.Context) -> None:
        lines: list = [
            "**Shorthands for commands used to fetch data related to Git and GitHub**",
            f"`git license` {Mgr.e.arrow} `git info -L`",
            f"`git repo --download` {Mgr.e.arrow} `git repo -dl`",
            f"`git lines` {Mgr.e.arrow} `git -l`"
        ]
        embed = discord.Embed(
            title=f"{Mgr.e.err}  Utility Aliases",
            color=0xefefef,
            description="\n".join(lines)
        )
        embed.set_footer(text=f"You can find usage of these commands by typing git --help utility")
        await ctx.send(embed=embed)

    @alias_command.command(name="config", aliases=['-config', '--config'])
    @commands.cooldown(15, 30, commands.BucketType.user)
    async def config_aliases(self, ctx: commands.Context) -> None:
        lines: list = [
            "Shorthands for commands used to store your preferred orgs, repos, users and feeds",
            f"`git config` {Mgr.e.arrow} `git cfg`",
            f"`git config -show` {Mgr.e.arrow} `git cfg -S`",
            f"`git config --user` {Mgr.e.arrow} `git cfg -U`",
            f"`git config --org` {Mgr.e.arrow} `git cfg -O`",
            f"`git config --repo` {Mgr.e.arrow} `git cfg -R`",
            f"`git config --feed` {Mgr.e.arrow} `git cfg -F`"
        ]
        embed = discord.Embed(
            title=f"{Mgr.e.err}  Config Aliases",
            color=0xefefef,
            description="\n".join(lines)
        )
        embed.set_footer(text=f"You can find usage of these commands by typing git config")
        await ctx.send(embed=embed)

    @alias_command.command(name="info", aliases=["-info", "--info"])
    @commands.cooldown(15, 30, commands.BucketType.user)
    async def info_command_aliases(self, ctx: commands.Context) -> None:
        lines: list = [
            "Shorthands for commands not tied to GitHub itself",
            f"`git uptime` {Mgr.e.arrow} `git up`",
            f"`git ping` {Mgr.e.arrow} `git p`"
        ]
        embed = discord.Embed(
            title=f"{Mgr.e.err}  Info Aliases",
            color=0xefefef,
            description="\n".join(lines)
        )
        embed.set_footer(text=f"You can find usage of these commands by typing git help info")
        await ctx.send(embed=embed)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Help(bot))
