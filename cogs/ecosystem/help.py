import discord
from discord.ext import commands


class Help(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot
        self.e: str = "<:ge:767823523573923890>"
        self.ga: str = "<:ga:768064843176738816>"

    @commands.group(name='--help', aliases=['help', '-H'])
    @commands.cooldown(15, 30, commands.BucketType.user)
    async def help_command(self, ctx: commands.Context) -> None:
        if ctx.invoked_subcommand is None:
            lines: list = ["In this section you'll find info and usage of my commands.",
                           "\n**You can access specific parts by typing:**",
                           "`git help github` to fetch information from GitHub",
                           "`git help info` for commands that provide information about the bot itself",
                           "`git help config` to store your preferred orgs, repos, user and feeds",
                           "`git help utility` for other useful commands",
                           "\n**If you have any problems,** [**join the support server!**](https://discord.gg/3e5fwpA)"]
            embed = discord.Embed(
                title=f"{self.e}  Help",
                color=0xefefef,
                description="\n".join(lines)
            )
            embed.set_footer(text=f"You can find a list of aliases by using the git --aliases command")
            await ctx.send(embed=embed)

    @help_command.command(name='github', aliases=['-github', '--github'])
    @commands.cooldown(15, 30, commands.BucketType.user)
    async def github_help(self, ctx: commands.Context) -> None:
        lines: list = ["**Words in curly braces symbolize arguments that the command requires**",
                       "`git user -info {username}` - get information about a user",
                       "`git user -repos {username}` - view a user's repos",
                       "`git gist {username}` - view a user's gists",
                       "`git org -info {organization}` - get info about an organization",
                       "`git org -repos {organization}` - view an organization's repos",
                       "\n**Important!** Repo commands that follow, require the exact syntax of `username/repo-name` "
                       "in place of the `{repo}` argument, ex. `itsmewulf/GitHub-Discord`",
                       "\n`git issue {repo} {issue number}` - get detailed info on an issue",
                       "`git pr {repo} {pr number}` - get detailed info on a pull request",
                       "`git repo -info {repo}` - get info about a repository",
                       "`git repo -files {repo}` - get the repo's file structure",
                       "`git repo -issues {repo} (state)` - get 10 latest issues from a repo (state defaults to "
                       "OPEN). If no repo is passed, the stored one is used."]
        embed = discord.Embed(
            title=f"{self.e}  GitHub Help",
            color=0xefefef,
            description="\n".join(lines)
        )
        embed.set_footer(text=f"You can find a list of aliases by using the git --aliases command")
        await ctx.send(embed=embed)

    @help_command.command(name='utility', aliases=['-utility', '--utility'])
    @commands.cooldown(15, 30, commands.BucketType.user)
    async def utlity_help(self, ctx: commands.Context) -> None:
        lines: list = ["These commands let you fetch various data related to Git and GitHub.",
                       "`git license {license}` - get info about a license",
                       "`git lines {link}` - get the lines mentioned in a GitHub or GitLab link",
                       "`git info {link}` - automatically inspect a link and get info on it"]
        embed = discord.Embed(
            title=f"{self.e}  Utility Help",
            color=0xefefef,
            description="\n".join(lines)
        )
        embed.set_footer(text=f"You can find a list of aliases by using the git --aliases command")
        await ctx.send(embed=embed)

    @help_command.command(name='config', aliases=['-config', '--config'])
    @commands.cooldown(15, 30, commands.BucketType.user)
    async def config_help(self, ctx: commands.Context) -> None:
        lines: list = ["**These commands affect the behavior of the Bot.**",
                       "`git config` - get detailed info on your options",
                       "`git config -show` - shows your current settings"]
        embed = discord.Embed(
            title=f"{self.e}  Config Help",
            color=0xefefef,
            description="\n".join(lines)
        )
        embed.set_footer(text=f"You can find a list of aliases by using the git --aliases command")
        await ctx.send(embed=embed)

    @help_command.command(name="info", aliases=["-info", "--info"])
    @commands.cooldown(15, 30, commands.BucketType.user)
    async def info_help(self, ctx: commands.Context) -> None:
        lines: list = ["These commands have no ties to GitHub and focus on the Bot itself.",
                       "`git aliases` - get a list of command shorthands",
                       "`git privacy` - the Bot's privacy policy",
                       "`git vote` - vote for the Bot!",
                       "`git stats` - some stats regarding the Bot",
                       "`git uptime` - see the time since the last restart of the Bot",
                       "`git ping` - see the Bot's latency"]

        embed = discord.Embed(
            title=f"{self.e}  Info Help",
            color=0xefefef,
            description="\n".join(lines)
        )
        embed.set_footer(text=f"You can find a list of aliases by using the git --aliases command")
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
                title=f"{self.e}  Aliases",
                color=0xefefef,
                description="\n".join(lines)
            )
            embed.set_footer(text=f"You can find usage of these commands by typing git --help")
            await ctx.send(embed=embed)

    @alias_command.command(name="github", aliases=['-github', '--github'])
    @commands.cooldown(15, 30, commands.BucketType.user)
    async def github_aliases(self, ctx: commands.Context) -> None:
        lines: list = ["Some commands default to their `info` variant if it's omitted:",
                       f"`git user -info` {self.ga} `git user`",
                       f"`git repo -info` {self.ga} `git repo`",
                       f"`git org -info` {self.ga} `git org`",
                       f"There are generic aliases as well:",
                       f"`git user -repos` {self.ga} `git user -r`",
                       f"`git org -repos` {self.ga} `git org -r`",
                       f"`git issue` {self.ga} `git i`"]
        embed = discord.Embed(
            title=f"{self.e}  GitHub Aliases",
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
            f"`git license` {self.ga} `git info -L`",
            f"`git repo --download` {self.ga} `git repo -dl`",
            f"`git lines` {self.ga} `git -l`"
        ]
        embed = discord.Embed(
            title=f"{self.e}  Utility Aliases",
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
            f"`git config` {self.ga} `git cfg`",
            f"`git config -show` {self.ga} `git cfg -S`",
            f"`git config --user` {self.ga} `git cfg -U`",
            f"`git config --org` {self.ga} `git cfg -O`",
            f"`git config --repo` {self.ga} `git cfg -R`",
            f"`git config --feed` {self.ga} `git cfg -F`"
        ]
        embed = discord.Embed(
            title=f"{self.e}  Config Aliases",
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
            f"`git uptime` {self.ga} `git up`",
            f"`git ping` {self.ga} `git p`"
        ]
        embed = discord.Embed(
            title=f"{self.e}  Info Aliases",
            color=0xefefef,
            description="\n".join(lines)
        )
        embed.set_footer(text=f"You can find usage of these commands by typing git help info")
        await ctx.send(embed=embed)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Help(bot))
