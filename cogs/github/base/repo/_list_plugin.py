from typing import Optional, Iterable
from lib.typehints import GitHubRepository
from lib.structs import GitBotEmbed, GitHubInfoSelectView
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
        repo: Optional[str] = await ctx.bot.mgr.db.users.getitem(ctx, 'repo')
        if not repo:
            await ctx.error(ctx.l.generic.nonexistent.repo.qa)
            return
        stored: bool = True
    issues: list | Iterable[dict] = await ctx.bot.mgr.reverse(
        await ctx.bot.github.get_last_issues_by_state(repo, state=state.upper()))
    if not issues:
        await handle_none(ctx, 'issue', stored, lstate)
        return

    issue_strings: list[str] = [make_string(ctx, repo, i, 'issues') for i in issues]

    embed: GitBotEmbed = GitBotEmbed(
            color=ctx.bot.mgr.c.rounded,
            title=ctx.fmt('title', f'`{lstate}`', repo),
            url=f'https://github.com/{repo}/issues',
            description='\n'.join(issue_strings),
            footer=ctx.l.repo.issues.footer_tip
    )

    async def _callback(_ctx: GitBotContext, selected_issue: dict):
        ctx.data = await ctx.bot.github.get_issue('', 0, selected_issue, True)
        await ctx.invoke(ctx.bot.get_command('issue'), repo)

    await ctx.send(embed=embed, view=GitHubInfoSelectView(
            ctx, 'issue', '#{number} - {author login}', '{title}', issues, _callback
    ))


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
        repo: Optional[str] = await ctx.bot.mgr.db.users.getitem(ctx, 'repo')
        if not repo:
            await ctx.error(ctx.l.generic.nonexistent.repo.qa)
            return
        stored: bool = True
    prs: list | Iterable[dict] = await ctx.bot.mgr.reverse(
        await ctx.bot.github.get_last_pull_requests_by_state(repo, state=state.upper()))
    if not prs:
        await handle_none(ctx, 'pull request', stored, lstate)
        return

    pr_strings: list[str] = [make_string(ctx, repo, pr, 'pull') for pr in prs]

    embed: GitBotEmbed = GitBotEmbed(
            color=ctx.bot.mgr.c.rounded,
            title=ctx.fmt('title', f'`{lstate}`', repo),
            url=f'https://github.com/{repo}/pulls',
            description='\n'.join(pr_strings),
            footer=ctx.l.repo.pulls.footer_tip
    )

    async def _callback(_ctx: GitBotContext, selected_pr: dict):
        ctx.data = await ctx.bot.github.get_pull_request('', 0, selected_pr)
        await ctx.invoke(ctx.bot.get_command('pr'), repo)

    await ctx.send(embed=embed, view=GitHubInfoSelectView(
            ctx, 'pull request', '#{number} - {author login}', '{title}', prs, _callback
    ))


async def handle_none(ctx: GitBotContext, item: str, stored: bool, state: str) -> None:
    if item is None:
        if stored:
            await ctx.bot.mgr.db.users.delitem(ctx, 'repo')
            await ctx.error(ctx.l.generic.nonexistent.repo.saved_repo_unavailable)
        else:
            await ctx.error(ctx.l.generic.nonexistent.repo.base)
    else:
        await ctx.error(ctx.bot.mgr.get_nested_key(ctx.l.generic, f'nonexistent repo no_'
                                                                  f'{"issues" if item == "issue" else "pulls"}'
                                                                  f'_with_state{"_qa" if stored else ""}')
                        .format(f'`{state}`'))


def make_string(ctx: GitBotContext, repo: GitHubRepository, issue_or_pr: dict, path: str) -> str:
    url: str = f'https://github.com/{repo}/{path}/{issue_or_pr["number"]}/'
    return f'[`#{issue_or_pr["number"]}`]({url}) **|** [' \
           f'{ctx.bot.mgr.truncate(issue_or_pr["title"], 70)}]({url})'
