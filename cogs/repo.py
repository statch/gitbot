import discord
import datetime
import re
from discord.ext import commands
from typing import Union, Optional
from cfg import bot_config

Git = bot_config.Git
md_emoji_re = re.compile(r':.*:', re.IGNORECASE)


class Repo(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot
        self.emoji: str = '<:github:772040411954937876>'
        self.square: str = ":white_small_square:"
        self.f: str = "<:file:762378114135097354>"
        self.fd: str = "<:folder:762378091497914398>"
        self.e: str = "<:ge:767823523573923890>"

    @commands.group(name='repo', aliases=['r'], invoke_without_command=True)
    async def repo_command_group(self, ctx: commands.Context, repo: Optional[str] = None) -> None:
        info_command: commands.Command = self.bot.get_command(f'repo --info')
        if not repo:
            stored = await self.bot.get_cog('Config').getitem(ctx, 'repo')
            if stored:
                ctx.invoked_with_stored = True
                await ctx.invoke(info_command, repo=stored)
        else:
            await ctx.invoke(info_command, repo=repo)

    @repo_command_group.command(name='--info', aliases=['-i', 'info', 'i'])
    @commands.cooldown(15, 30, commands.BucketType.user)
    async def repo_info_command(self, ctx: commands.Context, repo: Optional[str]) -> None:
        r: Union[dict, None] = await Git.get_repo(str(repo))
        if not r:
            if hasattr(ctx, 'invoked_with_stored'):
                await self.bot.get_cog('Config').delete_field(ctx, 'repo')
                await ctx.send(
                    f"{self.e}  The repo you had saved changed its name or was deleted. Please **re-add it** "
                    f"using `git --config -repo`")
            else:
                await ctx.send(f"{self.emoji} This repo **doesn't exist!**")
            return None

        embed = discord.Embed(
            color=int(r['primaryLanguage']['color'][1:], 16) if r['primaryLanguage'] else 0xefefef,
            title=f"{repo}",
            description=None,
            url=r['url']
        )

        watch: int = r['watchers']['totalCount']
        star: int = r['stargazers']['totalCount']
        open_issues: int = r['issues']['totalCount']

        if r['description'] is not None and len(r['description']) != 0:
            embed.add_field(name=":notepad_spiral: Description:",
                            value=f"```{re.sub(md_emoji_re, '', r['description']).strip()}```")

        watchers: str = f"Has [{watch} watchers]({r['url']}/watchers)" if watch != 1 else f"Has [one watcher]({r['url']}/watchers) "
        if watch == 0:
            watchers: str = f"Has no watchers"
        stargazers: str = f"no stargazers\n" if star == 0 else f"[{star} stargazers]({r['url']}/stargazers)\n"
        if star == 1:
            stargazers: str = f"[one stargazer]({r['url']}/stargazers)\n"

        watchers_stargazers: str = f"{watchers} and {stargazers}"

        issues: str = f'Doesn\'t have any [open issues]({r["url"]}/issues)\n' if open_issues == 0 else f"Has [{open_issues} open issues]({r['url']}/issues)\n"
        if open_issues == 1:
            issues: str = f"Has only one [open issue]({r['url']}/issues)\n"

        forks: str = f"No one has forked this repo, yet\n" if r[
                                                                  'forkCount'] == 0 else f"Has been forked [{r['forkCount']} times]({r['url']}/network/members)\n"
        if r['forkCount'] == 1:
            forks: str = f"It's been forked [only once]({r['url']}/network/members)\n"
        forked = ""
        if 'isFork' in r and r['isFork'] is True:
            forked = f"This repo is a fork of [{r['parent']['nameWithOwner']}]({r['parent']['url']})\n"

        created_at = f"Created on {datetime.datetime.strptime(r['createdAt'], '%Y-%m-%dT%H:%M:%SZ').strftime('%e, %b %Y')}\n"

        languages = ""
        if lang := r['primaryLanguage']:
            if r['languages'] == 1:
                languages = f'Written mainly using {lang["name"]}'
            else:
                languages = f'Written in {r["languages"]} languages, mainly in {lang["name"]}'

        info: str = f"{created_at}{issues}{forks}{watchers_stargazers}{forked}{languages}"
        embed.add_field(name=":mag_right: Info:", value=info, inline=False)

        homepage: tuple = (r['homepageUrl'] if 'homepageUrl' in r and r['homepageUrl'] else None, "Homepage")
        links: list = [homepage]
        link_strings: list = []
        for lnk in links:
            if lnk[0] is not None and len(lnk[0]) != 0:
                link_strings.append(f"- [{lnk[1]}]({lnk[0]})")
        if len(link_strings) != 0:
            embed.add_field(name=f":link: Links:", value='\n'.join(link_strings), inline=False)

        if r['topics'][0] and len(r['topics'][0]) > 1:
            topic_strings = ' '.join(
                [f"[`{t['topic']['name']}`]({t['url']})" for t in r['topics'][0]])
            more = f' `+{r["topics"][1] - 10}`' if r["topics"][1] > 10 else ""
            embed.add_field(name=f':label: Topics:', value=topic_strings + more)

        if r['graphic']:
            embed.set_image(url=r['graphic'])

        if 'licenseInfo' in r and r['licenseInfo'] is not None and r['licenseInfo']["name"].lower() != 'other':
            embed.set_footer(text=f'Licensed under the {r["licenseInfo"]["name"]}')

        await ctx.send(embed=embed)

    @repo_command_group.command(name='--files', aliases=['-f', '-src', '-s', '-fs'])
    @commands.cooldown(15, 30, commands.BucketType.user)
    async def repo_files_command(self, ctx: commands.Context, repo: str) -> None:
        is_tree: bool = False
        if repo.count('/') > 1:
            repo = "/".join(repo.split("/", 2)[:2])
            file = repo[len(repo):]
            src = await Git.get_tree_file(repo, file)
            is_tree = True
        else:
            src = await Git.get_repo_files(repo)
        if not src:
            if is_tree:
                await ctx.send(f"{self.emoji} This path **doesn't exist!**")
            else:
                await ctx.send(f"{self.emoji} This repo **doesn't exist!**")
            return

        files: list = [f"{self.f}  [{f['name']}]({f['html_url']})" if f[
                                                                          'type'] == 'file' else f"{self.fd}  [{f['name']}]({f['html_url']})"
                       for f in src[:15]]
        if is_tree:
            link: str = str(src[0]['_links']['html'])
            link = link[:link.rindex('/')]
        else:
            link: str = f"https://github.com/{repo}"
        embed = discord.Embed(
            color=0xefefef,
            title=f"{repo}" if len(repo) <= 60 else "/".join(repo.split("/", 2)[:2]),
            description='\n'.join(files),
            url=link
        )
        if len(files) > 15:
            more: str = str(len(files) - 15) if len(files) - 15 < 15 else "15+"
            embed.set_footer(text=f"View {more} more on GitHub")
        await ctx.send(embed=embed)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Repo(bot))
