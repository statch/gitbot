import discord
from lib.globs import Mgr
from discord.ext import commands


class Help(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot

    @commands.group(name='--help', aliases=['help', '-H', '-help'])
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
                       f"`git user -info {{{ctx.l.argument_placeholders.user}}}` - {ctx.l.help.github.commands.user.info}",
                       f"`git user -repos {{{ctx.l.argument_placeholders.user}}}` - {ctx.l.help.github.commands.user.repos}",
                       f"`git gist {{{ctx.l.argument_placeholders.user}}}` - {ctx.l.help.github.commands.gist}",
                       f"`git org -info {{{ctx.l.argument_placeholders.org}}}` - {ctx.l.help.github.commands.org.info}",
                       f"`git org -repos {{{ctx.l.argument_placeholders.org}}}` - {ctx.l.help.github.commands.org.repos}",
                       f"\n{ctx.l.help.github.commands.repo_argument_note}",
                       f"\n`git issue {{{ctx.l.argument_placeholders.repo}}} {{{ctx.l.argument_placeholders.issue_number}}}` - {ctx.l.help.github.commands.issue}",
                       f"`git pr {{{ctx.l.argument_placeholders.repo}}} {{{ctx.l.argument_placeholders.pr_number}}}` - {ctx.l.help.github.commands.pr}",
                       f"`git repo -info {{{ctx.l.argument_placeholders.repo}}}` - {ctx.l.help.github.commands.repo.info}",
                       f"`git repo -files {{{ctx.l.argument_placeholders.repo}}}` - {ctx.l.help.github.commands.repo.files}",
                       f"`git repo -issues {{{ctx.l.argument_placeholders.repo}}} ({ctx.l.argument_placeholders.state})` - {ctx.l.help.github.commands.repo.issues}",
                       f"`git repo -pulls {{{ctx.l.argument_placeholders.repo}}} ({ctx.l.argument_placeholders.state})` - {ctx.l.help.github.commands.repo.pulls}"]

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
                       f"`git commits` - {ctx.l.help.utility.commands.commits}",
                       f"`git loc {{{ctx.l.argument_placeholders.repo}}}` - {ctx.l.help.utility.commands.loc}",
                       f"`git license {{{ctx.l.argument_placeholders.license}}}` - {ctx.l.help.utility.commands.license}",
                       f"`git snippet {{{ctx.l.argument_placeholders.link_or_codeblock}}}` - {ctx.l.help.utility.commands.snippet}",
                       f"`git snippet --raw {{{ctx.l.argument_placeholders.link}}}` - {ctx.l.help.utility.commands.snippet_raw}",
                       f"`git info {{{ctx.l.argument_placeholders.link}}}` - {ctx.l.help.utility.commands.info}"]
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
    async def alias_command_group(self, ctx: commands.Context) -> None:
        if ctx.invoked_subcommand is None:
            lines: list = [ctx.l.aliases.default.description,
                           f"`git aliases github` - {ctx.l.aliases.default.sections.github}",
                           f"`git aliases info` - {ctx.l.aliases.default.sections.info}",
                           f"`git aliases config` - {ctx.l.aliases.default.sections.config}",
                           f"`git aliases utility` - {ctx.l.aliases.default.sections.utility}"]
            embed = discord.Embed(
                title=f"{Mgr.e.err}  {ctx.l.aliases.default.title}",
                color=0xefefef,
                description="\n".join(lines)
            )
            embed.set_footer(text=ctx.l.aliases.default.footer)
            await ctx.send(embed=embed)

    @alias_command_group.command(name="github", aliases=['-github', '--github'])
    @commands.cooldown(15, 30, commands.BucketType.user)
    async def github_aliases(self, ctx: commands.Context) -> None:
        lines: list = [ctx.l.aliases.github.argument_omitted,
                       f"`git user -info` {Mgr.e.arrow} `git user`",
                       f"`git repo -info` {Mgr.e.arrow} `git repo`",
                       f"`git org -info` {Mgr.e.arrow} `git org`",
                       ctx.l.aliases.github.generic_aliases,
                       f"`git user -repos` {Mgr.e.arrow} `git user -r`",
                       f"`git org -repos` {Mgr.e.arrow} `git org -r`",
                       f"`git issue` {Mgr.e.arrow} `git i`"]
        embed = discord.Embed(
            title=f"{Mgr.e.err}  {ctx.l.aliases.github.title}",
            color=0xefefef,
            description="\n".join(lines)
        )
        embed.set_footer(text=ctx.l.aliases.github.footer)
        await ctx.send(embed=embed)

    @alias_command_group.command(name="utility", aliases=['-utility', '--utility'])
    @commands.cooldown(15, 30, commands.BucketType.user)
    async def utility_aliases(self, ctx: commands.Context) -> None:
        lines: list = [
            ctx.l.aliases.utility.description,
            f"`git license` {Mgr.e.arrow} `git info -L`",
            f"`git repo --download` {Mgr.e.arrow} `git repo -dl`",
            f"`git lines` {Mgr.e.arrow} `git -l`"
        ]
        embed = discord.Embed(
            title=f"{Mgr.e.err}  {ctx.l.aliases.utility.title}",
            color=0xefefef,
            description="\n".join(lines)
        )
        embed.set_footer(text=ctx.l.aliases.utility.footer)
        await ctx.send(embed=embed)

    @alias_command_group.command(name="config", aliases=['-config', '--config'])
    @commands.cooldown(15, 30, commands.BucketType.user)
    async def config_aliases(self, ctx: commands.Context) -> None:
        lines: list = [
            ctx.l.aliases.config.description,
            f"`git config` {Mgr.e.arrow} `git cfg`",
            f"`git config -show` {Mgr.e.arrow} `git cfg -S`",
            f"`git config --user` {Mgr.e.arrow} `git cfg -U`",
            f"`git config --org` {Mgr.e.arrow} `git cfg -O`",
            f"`git config --repo` {Mgr.e.arrow} `git cfg -R`",
            f"`git config --feed` {Mgr.e.arrow} `git cfg -F`"
        ]
        embed = discord.Embed(
            title=f"{Mgr.e.err}  {ctx.l.aliases.config.title}",
            color=0xefefef,
            description="\n".join(lines)
        )
        embed.set_footer(text=ctx.l.aliases.config.footer)
        await ctx.send(embed=embed)

    @alias_command_group.command(name="info", aliases=["-info", "--info"])
    @commands.cooldown(15, 30, commands.BucketType.user)
    async def info_command_aliases(self, ctx: commands.Context) -> None:
        lines: list = [
            ctx.l.aliases.info.description,
            f"`git uptime` {Mgr.e.arrow} `git up`",
            f"`git ping` {Mgr.e.arrow} `git p`"
        ]
        embed = discord.Embed(
            title=f"{Mgr.e.err}  {ctx.l.aliases.info.title}",
            color=0xefefef,
            description="\n".join(lines)
        )
        embed.set_footer(text=ctx.l.aliases.info.footer)
        await ctx.send(embed=embed)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Help(bot))
