import discord
import datetime
from typing import Optional, Union
from babel.dates import format_date
from lib.globs import Git, Mgr
from lib.utils.decorators import normalize_repository
from discord.ext import commands


class Issue(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot

    @commands.command(name='issue', aliases=['-issue', 'i'])
    @commands.cooldown(10, 30, commands.BucketType.user)
    @normalize_repository
    async def issue_command(self, ctx: commands.Context, repo: str, issue_number: str = None) -> None:
        ctx.fmt.set_prefix('issue')
        if hasattr(ctx, 'data'):
            issue: dict = getattr(ctx, 'data')
            issue_number: Union[int, str] = issue['number']
        else:
            if not issue_number:
                if not repo.isnumeric():
                    await ctx.err(ctx.l.issue.stored_no_number)
                    return
                num: str = repo
                stored: Optional[str] = await Mgr.db.users.getitem(ctx, 'repo')
                if stored:
                    repo: str = stored
                    issue_number: str = num
                else:
                    await ctx.err(ctx.l.generic.nonexistent.repo.qa)
                    return

            try:
                issue: Union[dict, str] = await Git.get_issue(repo, int(issue_number))
            except ValueError:
                await ctx.err(ctx.l.issue.second_argument_number)
                return
            if isinstance(issue, str):
                if issue == 'repo':
                    await ctx.err(ctx.l.generic.nonexistent.repo.base)
                else:
                    await ctx.err(ctx.l.generic.nonexistent.issue_number)
                return

        em: str = f"<:issue_open:788517560164810772>"
        if issue['state'].lower() == 'closed':
            em: str = '<:issue_closed:788517938168594452>'
        embed: discord.Embed = discord.Embed(
            color=0xefefef,
            title=f"{em}  {issue['title']} #{issue_number}",
            url=issue['url']
        )
        if all(['body' in issue, issue['body'], len(issue['body'])]):
            body: Optional[str] = str(issue['body']).strip()
            if len(body) > 512:
                body: str = body[:512]
                body: str = f"{body[:body.rindex(' ')]}...".strip()
        else:
            body = None
        if body:
            embed.add_field(name=f':notepad_spiral: {ctx.l.issue.glossary[0]}:', value=f"```{body}```", inline=False)

        user: str = ctx.fmt('created_at',
                            f"[{issue['author']['login']}]({issue['author']['url']})",
                            format_date(datetime.datetime.strptime(issue['createdAt'],
                                                                   '%Y-%m-%dT%H:%M:%SZ').date(),
                                                                   'full',
                                                                   locale=ctx.l.meta.name))

        if issue['closed']:
            closed: str = '\n' + ctx.fmt('closed_at', format_date(datetime.datetime.strptime(issue['closedAt'],
                                                                  '%Y-%m-%dT%H:%M:%SZ').date(),
                                                                  'full',
                                                                  locale=ctx.l.meta.name)) + '\n'
        else:
            closed: str = '\n'

        assignees: str = ctx.fmt('assignees plural', issue['assigneeCount'])
        if issue['assigneeCount'] == 1:
            assignees: str = ctx.l.issue.assignees.singular
        elif issue['assigneeCount'] == 0:
            assignees: str = ctx.l.issue.assignees.no_assignees

        comments: str = ctx.fmt('comments plural', issue['commentCount'])
        if issue['commentCount'] == 1:
            comments: str = ctx.l.issue.comments.singular
        elif issue['commentCount'] == 0:
            comments: str = ctx.l.issue.comments.no_comments

        comments_and_assignees: str = f"{comments} {ctx.l.issue.linking_word} {assignees}"

        participants: str = f"\n{ctx.fmt('participants plural', issue['participantCount'])}" if \
            issue['participantCount'] != 1 else f"\n{ctx.l.issue.participants.singular}"

        info: str = f"{user}{closed}{comments_and_assignees}{participants}"

        embed.add_field(name=f':mag_right: {ctx.l.issue.glossary[1]}:', value=info, inline=False)

        if issue['labels']:
            embed.add_field(name=f':label: {ctx.l.issue.glossary[2]}:', value=' '.join([f"`{lb}`" for lb in issue['labels']]))

        embed.set_thumbnail(url=issue['author']['avatarUrl'])
        await ctx.send(embed=embed)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Issue(bot))
