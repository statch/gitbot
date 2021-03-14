import discord
from discord.ext import commands
from typing import Optional, List
from core.globs import Git, Mgr
from asyncio import TimeoutError

err: str = "<:ge:767823523573923890>"


async def issue_list(ctx: commands.Context, repo: Optional[str] = None, state: str = 'open') -> None:
    if (lstate := state.lower()) not in ('open', 'closed'):
        await ctx.send(f'{err} `{state}` is not a **valid issue state!** (Try `open` or `closed`)')
        return
    if repo and (s := repo.lower()) in ('open', 'closed'):
        state, lstate = s, s
        repo = None
    stored: bool = False
    if not repo:
        repo: Optional[str] = await ctx.bot.get_cog('Config').getitem(ctx, 'repo')
        if not repo:
            await ctx.send(f'{err} **You don\'t have a quick access repo configured!** (You didn\'t pass a '
                           f'repo into the command)')
            return
        stored: bool = True
    issues: List[dict] = await Mgr.reverse(await Git.get_last_issues_by_state(repo, state=f'[{state.upper()}]'))
    if not issues:
        await handle_none(ctx, 'issue', stored, lstate)
        return

    issue_strings: List[str] = [await make_string(repo, i, 'issues') for i in issues]

    embed: discord.Embed = discord.Embed(
        color=0xefefef,
        title=f'Latest {lstate} issues in `{repo}`',
        url=f'https://github.com/{repo}/issues',
        description='\n'.join(issue_strings)
    )

    embed.set_footer(text='You can quickly inspect a specific issue from the list by typing its number!\nYou can '
                          'type cancel to quit.')

    await ctx.send(embed=embed)

    while True:
        try:
            msg: discord.Message = await ctx.bot.wait_for('message',
                                                          check=lambda m: m.channel.id == ctx.channel.id and
                                                          m.author.id == ctx.author.id, timeout=30)
            if msg.content.lower() == 'cancel':
                return
            if not (issue := await Mgr.validate_number(num := msg.content, issues)):
                await ctx.send(f'{err} `{num}` is not a valid number **from the list!**', delete_after=7)
                continue
            else:
                ctx.data = await Git.get_issue('', 0, issue, True)
                await ctx.invoke(ctx.bot.get_command('issue'), repo)
                return
        except TimeoutError:
            return


async def pull_request_list(ctx: commands.Context, repo: Optional[str] = None, state: str = 'open') -> None:
    if (lstate := state.lower()) not in ('open', 'closed', 'merged'):
        await ctx.send(f'{err} `{state}` is not a **valid pull request state!** (Try `open`, `closed` or `merged`)')
        return
    if repo and (s := repo.lower()) in ('open', 'closed', 'merged'):
        state, lstate = s, s
        repo = None
    stored: bool = False
    if not repo:
        repo: Optional[str] = await ctx.bot.get_cog('Config').getitem(ctx, 'repo')
        if not repo:
            await ctx.send(f'{err} **You don\'t have a quick access repo configured!** (You didn\'t pass a '
                           f'repo into the command)')
            return
        stored: bool = True
    prs: List[dict] = await Mgr.reverse(await Git.get_last_pull_requests_by_state(repo, state=f'[{state.upper()}]'))
    if not prs:
        await handle_none(ctx, 'pull request', stored, lstate)
        return

    pr_strings: List[str] = [await make_string(repo, pr, 'pulls') for pr in prs]

    embed: discord.Embed = discord.Embed(
        color=0xefefef,
        title=f'Latest {lstate} pull requests in `{repo}`',
        url=f'https://github.com/{repo}/pulls',
        description='\n'.join(pr_strings)
    )

    embed.set_footer(text='You can quickly inspect a specific PR from the list by typing its number!\nYou can '
                          'type cancel to quit.')

    await ctx.send(embed=embed)

    while True:
        try:
            msg: discord.Message = await ctx.bot.wait_for('message',
                                                          check=lambda m: m.channel.id == ctx.channel.id and
                                                          m.author.id == ctx.author.id, timeout=30)
            if msg.content.lower() == 'cancel':
                return
            if not (pr := await Mgr.validate_number(num := msg.content, prs)):
                await ctx.send(f'{err} `{num}` is not a valid number **from the list!**', delete_after=7)
                continue
            else:
                ctx.data = await Git.get_pull_request('', 0, pr, True)
                await ctx.invoke(ctx.bot.get_command('pr'), repo)
                return
        except TimeoutError:
            return


async def handle_none(ctx: commands.Context, item: str, stored: bool, state: str) -> None:
    if item is None:
        if stored:
            await ctx.bot.get_cog('Config').delete_field(ctx, 'repo')
            await ctx.send(
                f'{err} You invoked the command with your stored repo, but it\'s unavailable. **Please re-add it.**')
        else:
            await ctx.send(f'{err}  This repo doesn\'t exist!')
    else:
        if not stored:
            await ctx.send(f'{err} This repo doesn\'t have any **{state} {item}s!**')
        else:
            await ctx.send(f'{err} Your saved repo doesn\'t have any **{state} {item}s!**')
    return


async def make_string(repo: str, item: dict, path: str) -> str:
    url: str = f'https://github.com/{repo}/{path}/{item["number"]}/'
    return f'[`#{item["number"]}`]({url}) **|** [' \
           f'{item["title"] if len(item["title"]) < 70 else item["title"][:67] + "..."}]({url})'
