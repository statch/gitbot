import discord
from discord.ext import commands
from typing import Optional
from core.globs import Git
from asyncio import TimeoutError

err: str = "<:ge:767823523573923890>"


async def issue_list(ctx: commands.Context, repo: Optional[str] = None, state: str = 'open') -> None:
    if (lstate := state.lower()) not in ('open', 'closed'):
        await ctx.send(f'{err} `{state}` is not a **valid issue state!** (Try `open` or `closed`)')
        return
    if repo and (s := repo.lower()) in ('open', 'closed'):
        state: str = s
        repo = None
    stored: bool = False
    if not repo:
        repo = await ctx.bot.get_cog('Config').getitem(ctx, 'repo')
        if not repo:
            await ctx.send(f'{err} **You don\'t have a quick access repo configured!** (You didn\'t pass a '
                           f'repo into the command)')
            return
        stored: bool = True
    issues: list = await Git.get_last_issues_by_state(repo, state=f'[{state.upper()}]')
    if not issues:
        if issues is None:
            if stored:
                await ctx.bot.get_cog('Config').delete_field(ctx, 'repo')
            await ctx.send(f'{err}  This repo doesn\'t exist!')
        else:
            if not stored:
                await ctx.send(f'{err} This repo doesn\'t have any open issues!')
            else:
                await ctx.send(f'{err} Your saved repo doesn\'t have any open issues!')
        return

    issue_strings: list = [make_issue_string(repo, i) for i in issues]

    embed: discord.Embed = discord.Embed(
        color=0xefefef,
        title=f'Latest {lstate} issues in `{repo}`',
        url=f'https://github.com/{repo}/issues',
        description='\n'.join(issue_strings)
    )

    embed.set_footer(text='You can quickly inspect a specific issue from the list by typing its number!\nYou can '
                          'type cancel to quit.')

    def validate_number(number: str) -> Optional[dict]:
        if number.startswith('#'):
            number: str = number[1:]
        try:
            number: int = int(number)
        except TypeError:
            return None
        matched = [i for i in issues if i['number'] == number]
        if matched:
            return matched[0]
        return None

    await ctx.send(embed=embed)

    while True:
        try:
            msg: discord.Message = await ctx.bot.wait_for('message',
                                                          check=lambda m: m.channel.id == ctx.channel.id and
                                                          m.author.id == ctx.author.id, timeout=30)
            if msg.content.lower() == 'cancel':
                return
            if not (issue := validate_number(num := msg.content)):
                await ctx.send(f'{err} `{num}` is not a valid number **from the list!**', delete_after=7)
                continue
            else:
                ctx.data = await Git.get_issue('', 0, issue, True)
                await ctx.invoke(ctx.bot.get_command('issue'), repo)
                return
        except TimeoutError:
            return


async def pull_request_list(ctx: commands.Context, repo: Optional[str] = None, state: str = 'open') -> None:  # TODO Implement pull_request_list
    pass


def make_issue_string(repo: str, issue: dict) -> str:
    url = f'https://github.com/{repo}/issues/{issue["number"]}/'
    return f'[`#{issue["number"]}`]({url}) **|** [' \
           f'{issue["title"] if len(issue["title"]) < 70 else issue["title"][:67] + "..."}]({url})'
