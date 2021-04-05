import discord
import datetime
import re
import io
from .list_plugin import *
from discord.ext import commands
from typing import Union, Optional
from core.globs import Git
from ext.regex import MD_EMOJI_RE


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
                await ctx.send(
                    f'{self.e}  You don\'t have a quick access repo configured! **Type** `git config` **to do it.**')
        else:
            await ctx.invoke(info_command, repo=repo)

    @repo_command_group.command(name='--info', aliases=['-i', 'info', 'i'])
    @commands.cooldown(15, 30, commands.BucketType.user)
    async def repo_info_command(self, ctx: commands.Context, repo: str) -> None:
        if hasattr(ctx, 'data'):
            r: dict = getattr(ctx, 'data')
        else:
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
            url=r['url']
        )

        embed.set_thumbnail(url=r['owner']['avatarUrl'])

        watch: int = r['watchers']['totalCount']
        star: int = r['stargazers']['totalCount']
        open_issues: int = r['issues']['totalCount']

        if r['description'] is not None and len(r['description']) != 0:
            embed.add_field(name=":notepad_spiral: Description:",
                            value=f"```{re.sub(MD_EMOJI_RE, '', r['description']).strip()}```")

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

    @commands.cooldown(15, 30, commands.BucketType.user)
    @repo_command_group.command(name='--files', aliases=['-f', 'files', '-files', '-s', '-src', '-fs', 'fs'])
    async def repo_files_command(self, ctx: commands.Context, repo_or_path: str) -> None:
        is_tree: bool = False
        if repo_or_path.count('/') > 1:
            repo = "/".join(repo_or_path.split("/", 2)[:2])
            file = repo_or_path[len(repo):]
            src = await Git.get_tree_file(repo, file)
            is_tree = True
        else:
            src = await Git.get_repo_files(repo_or_path)
        if not src:
            if is_tree:
                await ctx.send(f"{self.emoji} This path **doesn't exist!**")
            else:
                await ctx.send(f"{self.emoji} This repository **doesn't exist!**")
            return
        files: list = [f"{self.f}  [{f['name']}]({f['html_url']})" if f[
                                                                          'type'] == 'file' else f"{self.fd}  [{f['name']}]({f['html_url']})"
                       for f in src[:15]]
        if is_tree:
            link: str = str(src[0]['_links']['html'])
            link = link[:link.rindex('/')]
        else:
            link: str = f"https://github.com/{repo_or_path}"
        embed = discord.Embed(
            color=0xefefef,
            title=f"{repo_or_path}" if len(repo_or_path) <= 60 else "/".join(repo_or_path.split("/", 2)[:2]),
            description='\n'.join(files),
            url=link
        )
        if len(src) > 15:
            embed.set_footer(text=f"View {len(src) - 15} more on GitHub")
        await ctx.send(embed=embed)

    @repo_command_group.command(name='--download', aliases=['-download', 'download', '-dl'])
    @commands.max_concurrency(10, commands.BucketType.default, wait=False)
    @commands.cooldown(5, 30, commands.BucketType.user)
    async def download_command(self, ctx: commands.Context, repo: str) -> None:
        msg: discord.Message = await ctx.send(f"{self.emoji}  Give me a second while I download the file...")
        src_bytes: Optional[Union[bytes, bool]] = await Git.get_repo_zip(repo)
        if src_bytes is None:  # pylint: disable=no-else-return
            return await msg.edit(content=f"{self.e}  This repo **doesn't exist!**")
        elif src_bytes is False:
            return await msg.edit(
                content=f"{self.e}  That file is too big, **please download it directly here:**\nhttps://github.com/{repo}")
        io_obj: io.BytesIO = io.BytesIO(src_bytes)
        file: discord.File = discord.File(filename=f'{repo.replace("/", "-")}.zip', fp=io_obj)
        try:
            await ctx.send(file=file)
            await msg.edit(content=f'{self.emoji}  Here\'s the source code of **{repo}!**')
        except discord.errors.HTTPException:
            await msg.edit(
                content=f"{self.e} That file is too big, **please download it directly here:**\nhttps://github.com/{repo}")

    @repo_command_group.command(name='issues', aliases=['-issues', '--issues'])
    @commands.cooldown(5, 40, commands.BucketType.user)
    async def issue_list_command(self, ctx: commands.Context, repo: Optional[str] = None, state: str = 'open') -> None:
        await issue_list(ctx, repo, state)

    @repo_command_group.command(name='pulls', aliases=['-pulls', '--pulls', 'prs', '-prs', '--prs'])
    @commands.cooldown(5, 40, commands.BucketType.user)
    async def pull_request_list_command(self, ctx: commands.Context, repo: Optional[str] = None, state: str = 'open') -> None:
        await pull_request_list(ctx, repo, state)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Repo(bot))
