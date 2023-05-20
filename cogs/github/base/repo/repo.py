import discord
import re
import io
from ._list_plugin import issue_list, pull_request_list  # noqa
from discord.ext import commands
from typing import Optional
from lib.utils.decorators import normalize_repository, gitbot_group, uses_quick_access
from lib.utils.regex import MARKDOWN_EMOJI_RE
from lib.typehints import GitHubRepository
from lib.structs import GitBotEmbed, GitBot, EmbedPages
from lib.structs.discord.context import GitBotContext


class Repo(commands.Cog):
    def __init__(self, bot: GitBot):
        self.bot: GitBot = bot

    @gitbot_group(name='repo', aliases=['r'], invoke_without_command=True)
    @normalize_repository
    async def repo_command_group(self, ctx: GitBotContext, repo: Optional[GitHubRepository] = None) -> None:
        if not repo:
            stored: Optional[str] = await self.bot.mgr.db.users.getitem(ctx, 'repo')
            if stored:
                ctx.invoked_with_stored = True
                await ctx.invoke(self.repo_info_command, repo=stored)
            else:
                await ctx.error(ctx.l.generic.nonexistent.repo.qa)
        else:
            await ctx.invoke(self.repo_info_command, repo=repo)

    @repo_command_group.command(name='info', aliases=['i'])
    @commands.cooldown(15, 30, commands.BucketType.user)
    @normalize_repository
    async def repo_info_command(self, ctx: GitBotContext, repo: Optional[GitHubRepository] = None) -> None:
        if not repo:
            return await ctx.invoke(self.repo_command_group)
        ctx.fmt.set_prefix('repo info')
        if ctx.data:
            r: dict = getattr(ctx, 'data')
        else:
            r: Optional[dict] = await self.bot.github.get_repo(repo)
        if not r:
            if ctx.invoked_with_stored:
                await self.bot.mgr.db.users.delitem(ctx, 'repo')
                await ctx.error(ctx.l.generic.nonexistent.repo.qa_changed)
            else:
                await ctx.error(ctx.l.generic.nonexistent.repo.base)
            return

        embed: GitBotEmbed = GitBotEmbed(
                color=int(r['primaryLanguage']['color'][1:], 16) if r['primaryLanguage'] and r['primaryLanguage'][
                    'color'] else self.bot.mgr.c.rounded,
                title=repo,
                url=r['url'],
                thumbnail=r['owner']['avatarUrl']
        )

        watch: int = r['watchers']['totalCount']
        star: int = r['stargazers']['totalCount']
        open_issues: int = r['issues']['totalCount']

        if r['description'] is not None and len(r['description']) != 0:
            embed.add_field(name=f":notepad_spiral: {ctx.l.repo.info.glossary[0]}:",
                            value=f"```{re.sub(MARKDOWN_EMOJI_RE, '', r['description']).strip()}```")

        watchers: str = ctx.fmt('watchers plural', watch, f"{r['url']}/watchers") if watch != 1 else ctx.fmt(
            'watchers singular', f"{r['url']}/watchers")
        if watch == 0:
            watchers: str = ctx.l.repo.info.watchers.no_watchers
        stargazers: str = ctx.l.repo.info.stargazers.no_stargazers + '\n' if star == 0 else ctx.fmt('stargazers plural',
                                                                                                    star,
                                                                                                    f"{r['url']}/stargazers") + '\n'
        if star == 1:
            stargazers: str = ctx.fmt('stargazers singular', f"{r['url']}/stargazers") + '\n'

        watchers_stargazers: str = f"{watchers} {ctx.l.repo.info.linking_word} {stargazers}"

        issues: str = f'{ctx.l.repo.info.issues.no_issues}\n' if open_issues == 0 else ctx.fmt('issues plural',
                                                                                               open_issues,
                                                                                               f"{r['url']}/issues") + '\n'
        if open_issues == 1:
            issues: str = ctx.fmt('issues singular', f"{r['url']}/issues") + '\n'

        forks: str = ctx.l.repo.info.forks.no_forks + '\n' if r[
                                                                  'forkCount'] == 0 else ctx.fmt('forks plural',
                                                                                                 r['forkCount'],
                                                                                                 f"{r['url']}/network/members") + '\n'
        if r['forkCount'] == 1:
            forks: str = ctx.fmt('forks singular', f"{r['url']}/network/members") + '\n'
        forked = ""
        if 'isFork' in r and r['isFork'] is True:
            forked = ctx.fmt('fork_notice', f"[{r['parent']['nameWithOwner']}]({r['parent']['url']})") + '\n'

        created_at = ctx.fmt('created_at', self.bot.mgr.github_to_discord_timestamp(r['createdAt'])) + '\n'

        languages = ""
        if lang := r['primaryLanguage']:
            if r['languages'] == 1:
                languages = ctx.fmt('languages main', lang['name'])
            else:
                languages = ctx.fmt('languages with_num', r['languages'], lang['name'])

        info: str = f"{created_at}{issues}{forks}{watchers_stargazers}{forked}{languages}"
        embed.add_field(name=f":mag_right: {ctx.l.repo.info.glossary[1]}:", value=info)

        homepage: tuple = (
        r['homepageUrl'] if 'homepageUrl' in r and r['homepageUrl'] else None, ctx.l.repo.info.glossary[4])
        links: list = [homepage]
        if link_strings := [
            f"- [{lnk[1]}]({lnk[0]})"
            for lnk in links
            if lnk[0] is not None and len(lnk[0]) != 0
        ]:
            embed.add_field(name=f":link: {ctx.l.repo.info.glossary[2]}:", value='\n'.join(link_strings))

        if topics := self.bot.mgr.render_label_like_list(r['topics'][0],
                                                         name_and_url_knames_if_dict=('topic name', 'url'),
                                                         total_n=r['topics'][1]):
            embed.add_field(name=f':label: {ctx.l.repo.info.glossary[3]}:', value=topics)

        if r['graphic']:
            embed.set_image(url=r['graphic'])

        if 'licenseInfo' in r and r['licenseInfo'] is not None and r['licenseInfo']["name"].lower() != 'other':
            embed.set_footer(text=ctx.fmt('license', r["licenseInfo"]["name"]))

        await ctx.send(embed=embed, view_on_url=r['url'])

    @commands.cooldown(10, 30, commands.BucketType.user)
    @repo_command_group.command(name='files', aliases=['src', 'fs'])
    @uses_quick_access('repo', 'repo_or_path')
    async def repo_files_command(self, ctx: GitBotContext, repo_or_path: GitHubRepository | None = None, ref: str | None = None) -> None:
        ctx.fmt.set_prefix('repo files')
        if repo_or_path is not None and repo_or_path.startswith('/'):
            stored_repo: str = await ctx.bot.mgr.db.users.getitem(ctx, 'repo')
            if not stored_repo:
                await ctx.error(ctx.l.generic.nonexistent.repo.qa)
                return
            repo: str = stored_repo
            path: str = repo_or_path
            is_tree: bool = True
        else:
            repo: GitHubRepository = '/'.join(repo_or_path.split('/', 2)[:2])  # noqa
            is_tree: bool = repo_or_path != repo
            path: str = repo_or_path[len(repo):] if is_tree else None
        src: list = await self.bot.github.get_tree_file(repo, path, ref)
        if not src:
            if is_tree:
                await ctx.error(ctx.l.generic.nonexistent.path)
            elif ref:
                await ctx.error(ctx.l.generic.nonexistent.repo.or_ref.format(f'`{ref}`'))
            else:
                await ctx.error(ctx.l.generic.nonexistent.repo.base)
            return
        if is_tree and not isinstance(src, list):
            await ctx.error(ctx.fmt('not_a_directory', f'`{ctx.prefix}snippet`'))
            return
        if is_tree:
            link = (link := str(src[0]['_links']['html']))[:link.rindex('/')]
        else:
            link: str = f'https://github.com/{repo_or_path}'
        embeds: list = []

        def make_embed(items: list, footer: str | None = None) -> GitBotEmbed:
            return GitBotEmbed(
                    color=self.bot.mgr.c.rounded,
                    title=f'{self.bot.mgr.e.branch}  `{repo}`' + (f' ({ref})' if ref else ''),
                    description='\n'.join(
                            f'{self.bot.mgr.e.file}  [`{f["name"]}`]({f["html_url"]})' if f['type'] == 'file' else
                            f'{self.bot.mgr.e.folder}  [`{f["name"]}`]({f["html_url"]})' for f in items) + ('\n' + f'```{path}```' if path else ''),
                    url=link,
                    footer=footer
            )

        total = len(src)
        if len(src := sorted(src, key=lambda si: int(si['type'] == 'dir'), reverse=True)) > 200:
            src = src[:200]

        if len(src) > 20:
            for chunkno, chunk in enumerate(self.bot.mgr.chunks(src, 20)):
                if chunkno >= 10:
                    break

                range_: str = f'{chunkno * 20 + 1}-{min(((chunkno + 1) * 20, len(src)))}/{total}'
                embeds.append(make_embed(chunk, ctx.fmt('footer', range_)))

            if len(embeds) == 10:
                remaining = len(src) - ((len(embeds) - 1) * 20)
                footer = ctx.fmt('footer', f'{len(src) - remaining}-{len(src)}/{total}') + '\n' + ctx.fmt(
                        'footer_more', total - len(src)
                )
                embeds[-1].set_footer(text=footer)

        if not embeds:
            await ctx.send(embed=make_embed(src), view_on_url=link)
        else:
            await EmbedPages(embeds).start(ctx)

    @commands.command(name='repo-files-two-arg', hidden=True)
    @commands.cooldown(10, 30, commands.BucketType.user)
    async def repo_files_command_two_arg(self, ctx: GitBotContext, repo: str, ref: str, path: str) -> None:
        # different order due to how groups are captured in the regex
        await self.repo_files_command(
            ctx,
            repo_or_path=repo + (path if path.startswith('/') else f'/{path}'),
            ref=ref,
        )

    @repo_command_group.command(name='download', aliases=['dl'])
    @commands.max_concurrency(10)
    @commands.cooldown(5, 30, commands.BucketType.user)
    @normalize_repository
    async def download_command(self, ctx: GitBotContext, repo: GitHubRepository) -> None:
        ctx.fmt.set_prefix('repo download')
        msg: discord.Message = await ctx.send(f"{self.bot.mgr.e.github}  {ctx.l.repo.download.wait}")
        src_bytes: Optional[bytes | bool] = await self.bot.github.get_repo_zip(repo)
        if src_bytes is None:  # pylint: disable=no-else-return
            return await msg.edit(content=f"{self.bot.mgr.e.error}  {ctx.l.generic.nonexistent.repo.base}")
        elif src_bytes is False:
            return await msg.edit(
                    content=f"{self.bot.mgr.e.error}  {ctx.fmt('file_too_big', f'https://github.com/{repo}')}")
        io_obj: io.BytesIO = io.BytesIO(src_bytes)
        try:
            await ctx.send(file=discord.File(filename=f'{repo.replace("/", "-")}.zip', fp=io_obj))
            await msg.edit(content=f'{self.bot.mgr.e.checkmark}  {ctx.fmt("done", repo)}')
        except discord.errors.HTTPException:
            await msg.edit(
                    content=f"{self.bot.mgr.e.error}  {ctx.fmt('file_too_big', f'https://github.com/{repo}')}")

    @repo_command_group.command(name='issues')
    @commands.cooldown(5, 40, commands.BucketType.user)
    @normalize_repository
    async def issue_list_command(self,
                                 ctx: GitBotContext,
                                 repo: Optional[GitHubRepository] = None,
                                 state: str = 'open') -> None:
        await issue_list(ctx, repo, state)

    @repo_command_group.command(name='pulls', aliases=['prs', 'pull', 'pr'])
    @commands.cooldown(5, 40, commands.BucketType.user)
    @normalize_repository
    async def pull_request_list_command(self,
                                        ctx: GitBotContext,
                                        repo: Optional[GitHubRepository] = None,
                                        state: str = 'open') -> None:
        await pull_request_list(ctx, repo, state)

    # signature from cogs.github.numbered.commits.Commits.commits
    @repo_command_group.command(name='commits')
    @commands.cooldown(5, 40, commands.BucketType.user)
    async def commit_list_command(self,
                                  ctx: GitBotContext,
                                  repo: Optional[GitHubRepository] = None) -> None:
        await ctx.invoke(self.bot.get_command('commits'), repo=repo)

    @repo_command_group.command(name='loc')
    @commands.cooldown(8, 60)
    async def loc_command(self, ctx: GitBotContext, repo: GitHubRepository) -> None:
        await ctx.invoke(self.bot.get_command('loc'), repo=repo)


async def setup(bot: GitBot) -> None:
    await bot.add_cog(Repo(bot))
