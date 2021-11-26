import discord
import asyncio
from typing import Optional, Iterable
from lib.globs import Git, Mgr
from lib.typehints import GitHubRepository
from lib.structs import GitBotEmbed
from lib.structs.discord.context import GitBotContext

__all__: tuple = (
    'issue_list',
    'pull_request_list'
)


async def issue_list(ctx: GitBotContext, repo: Optional[GitHubRepository] = None, state: str = 'open') -> None:
    ctx.fmt.set_prefix('repo issues')
    if (lstate := state.lower()) not in ('open', 'closed'):
        await ctx.error(ctx.l.generic.issue.invalid_state.format(lstate))
        return
    if repo and (s := repo.lower()) in ('open', 'closed'):
        state, lstate = s, s
        repo = None
    stored: bool = False
    if not repo:
        repo: Optional[str] = await Mgr.db.users.getitem(ctx, 'repo')
        if not repo:
            await ctx.error(ctx.l.generic.nonexistent.repo.qa)
            return
        stored: bool = True
    issues: list | Iterable[dict] = await Mgr.reverse(await Git.get_last_issues_by_state(repo, state=state.upper()))
    if not issues:
        await handle_none(ctx, 'issue', stored, lstate)
        return

    issue_strings: list[str] = [make_string(repo, i, 'issues') for i in issues]

    embed: GitBotEmbed = GitBotEmbed(
        color=Mgr.c.rounded,
        title=ctx.fmt('title', f'`{lstate}`', repo),
        url=f'https://github.com/{repo}/issues',
        description='\n'.join(issue_strings),
        footer=ctx.l.repo.issues.footer_tip
    )

    await ctx.send(embed=embed)

    while True:
        try:
            msg: discord.Message = await ctx.bot.wait_for('message',
                                                          check=lambda m: m.channel.id == ctx.channel.id and
                                                          m.author.id == ctx.author.id, timeout=30)
            if msg.content.lower() == 'cancel':
                return
            if not (issue := await Mgr.validate_index(num := msg.content, issues)):
                await ctx.error(ctx.l.generic.invalid_index.format(f'`{num}`'), delete_after=7)
                continue
            else:
                ctx.data = await Git.get_issue('', 0, issue, True)
                await ctx.invoke(ctx.bot.get_command('issue'), repo)
                return
        except asyncio.TimeoutError:
            return


async def pull_request_list(ctx: GitBotContext, repo: Optional[GitHubRepository] = None, state: str = 'open') -> None:
    ctx.fmt.set_prefix('repo pulls')
    if (lstate := state.lower()) not in ('open', 'closed', 'merged'):
        await ctx.error(ctx.l.generic.pr.invalid_state.format(lstate))
        return
    if repo and (s := repo.lower()) in ('open', 'closed', 'merged'):
        state, lstate = s, s
        repo = None
    stored: bool = False
    if not repo:
        repo: Optional[str] = await Mgr.db.users.getitem(ctx, 'repo')
        if not repo:
            await ctx.error(ctx.l.generic.nonexistent.repo.qa)
            return
        stored: bool = True
    prs: list | Iterable[dict] = await Mgr.reverse(await Git.get_last_pull_requests_by_state(repo, state=state.upper()))
    if not prs:
        await handle_none(ctx, 'pull request', stored, lstate)
        return

    pr_strings: list[str] = [make_string(repo, pr, 'pull') for pr in prs]

    embed: GitBotEmbed = GitBotEmbed(
        color=Mgr.c.rounded,
        title=ctx.fmt('title', f'`{lstate}`', repo),
        url=f'https://github.com/{repo}/pulls',
        description='\n'.join(pr_strings),
        footer=ctx.l.repo.pulls.footer_tip
    )

    await ctx.send(embed=embed)

    while True:
        try:
            msg: discord.Message = await ctx.bot.wait_for('message',
                                                          check=lambda m: m.channel.id == ctx.channel.id and
                                                          m.author.id == ctx.author.id, timeout=30)
            if msg.content.lower() == 'cancel':
                return
            if not (pr := await Mgr.validate_index(num := msg.content, prs)):
                await ctx.error(ctx.l.generic.invalid_index.format(f'`{num}`'), delete_after=7)
                continue
            else:
                ctx.data = await Git.get_pull_request('', 0, pr)
                await ctx.invoke(ctx.bot.get_command('pr'), repo)
                return
        except asyncio.TimeoutError:
            return


async def handle_none(ctx: GitBotContext, item: str, stored: bool, state: str) -> None:
    if item is None:
        if stored:
            await Mgr.db.users.delitem(ctx, 'repo')
            await ctx.error(ctx.l.generic.nonexistent.repo.saved_repo_unavailable)
        else:
            await ctx.error(ctx.l.generic.nonexistent.repo.base)
    else:
        if not stored:
            if item == 'issue':
                await ctx.error(ctx.l.generic.nonexistent.repo.no_issues_with_state.format(f'`{state}`'))
            else:
                await ctx.error(ctx.l.generic.nonexistent.repo.no_pulls_with_state.format(f'`{state}`'))
        else:
            if item == 'issue':
                await ctx.error(ctx.l.generic.nonexistent.repo.no_issues_with_state_qa.format(f'`{state}`'))
            else:
                await ctx.error(ctx.l.generic.nonexistent.repo.no_pulls_with_state_qa.format(f'`{state}`'))


def make_string(repo: GitHubRepository, item: dict, path: str) -> str:
    url: str = f'https://github.com/{repo}/{path}/{item["number"]}/'
    return f'[`#{item["number"]}`]({url}) **|** [' \
           f'{Mgr.truncate(item["title"], 70)}]({url})'
