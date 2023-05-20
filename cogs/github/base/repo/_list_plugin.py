from typing import Optional, Iterable, Literal
from lib.typehints import GitHubRepository
from lib.structs import GitBotEmbed, GitHubInfoSelectView
from lib.structs.discord.context import GitBotContext

__all__: tuple = (
    'issue_list',
    'pull_request_list'
)


async def issue_list(ctx: GitBotContext, repo: Optional[GitHubRepository] = None, state: str = 'open') -> None:
    await joint_pr_issue_list_command(ctx, repo, state, 'issue')


async def pull_request_list(ctx: GitBotContext, repo: Optional[GitHubRepository] = None, state: str = 'open') -> None:
    return await joint_pr_issue_list_command(ctx, repo, state, 'pr')


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


def make_string(ctx: GitBotContext, repo: GitHubRepository, issue_or_pr: dict, path: str, pad_at: int) -> str:
    url: str = f'https://github.com/{repo}/{path}/{issue_or_pr["number"]}/'
    padding: str = ' ' * (pad_at - len(str(issue_or_pr['number'])))
    em: str = ctx.bot.mgr.e.get(f'pr_{issue_or_pr["state"].lower()}')
    return f'[`{padding}#{issue_or_pr["number"]}`]({url}) [' \
           f'{ctx.bot.mgr.truncate(issue_or_pr["title"], 70)}]({url})'


async def joint_pr_issue_list_command(ctx: GitBotContext, repo: Optional[GitHubRepository] = None, state: str = 'open',
                                      type_: str = Literal['issue', 'pr']):
    ctx.fmt.set_prefix(f'repo {"issues" if type_ == "issue" else "pulls"}')
    states: tuple[str, ...] = ('open', 'closed', 'merged') if type_ == 'pr' else ('open', 'closed')
    if (state_l := state.lower()) not in states:
        await ctx.error(ctx.l.generic[type_].invalid_state.format(state_l))
        return
    if repo and (s := repo.lower()) in states:
        state, state_l = s, s
        repo = None
    stored: bool = False
    if not repo:
        repo: Optional[str] = await ctx.bot.mgr.db.users.getitem(ctx, 'repo')
        if not repo:
            await ctx.error(ctx.l.generic.nonexistent.repo.qa)
            return
        stored: bool = True
    items: list | Iterable[dict] = await ctx.bot.mgr.reverse(
            await ctx.bot.github.get_last_pull_requests_by_state(repo, state=state.upper())
            if type_ == 'pr' else await ctx.bot.github.get_last_issues_by_state(repo, state=state.upper())
    )
    if not items:
        await handle_none(ctx, 'pull request' if type_ == 'pr' else 'issue', stored, state_l)
        return

    item_strings: list[str] = [
        make_string(
            ctx,
            repo,
            i,
            'pull' if type_ == 'pr' else 'issue',
            max(len(str(i['number'])) for i in items),
        )
        for i in items
    ]

    embed: GitBotEmbed = GitBotEmbed(
        color=ctx.bot.mgr.c.rounded,
        title=f"{ctx.bot.mgr.e.github} {ctx.bot.mgr.e.get(f'pr_{state_l}')}  "
        + ctx.fmt('title', f'`{state_l}`', f'`{repo}`'),
        url=f'https://github.com/{repo}/{"pulls" if type_ == "pr" else "issues"}',
        description='\n'.join(item_strings),
        footer=ctx.l.repo["pulls" if type_ == 'pr' else 'issues'].footer_tip,
    )

    async def _callback(_ctx: GitBotContext, selected: dict):
        ctx.data = (await ctx.bot.github.get_pull_request('', 0, selected) if type_ == 'pr' else
                    await ctx.bot.github.get_issue('', 0, selected, had_keys_removed=True))
        await ctx.invoke(ctx.bot.get_command(type_), repo)

    await ctx.send(embed=embed, view=GitHubInfoSelectView(
            ctx, 'pull request' if type_ == 'pr' else 'issue', '#{number} - {author login}', '{title}', items, _callback
    ))
