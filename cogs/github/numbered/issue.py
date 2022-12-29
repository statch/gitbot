import discord
from typing import Optional
from lib.utils.decorators import normalize_repository, gitbot_command
from discord.ext import commands
from lib.typehints import GitHubRepository
from lib.structs import GitBot
from lib.structs.discord.context import GitBotContext


class Issue(commands.Cog):
    def __init__(self, bot: GitBot):
        self.bot: GitBot = bot

    @gitbot_command(name='issue', aliases=['i'])
    @commands.cooldown(10, 30, commands.BucketType.user)
    @normalize_repository
    async def issue_command(self, ctx: GitBotContext, repo: GitHubRepository, issue_number: str = None) -> None:
        ctx.fmt.set_prefix('issue')
        if ctx.data:
            issue: dict = getattr(ctx, 'data')
            issue_number: int | str = issue['number']
        else:
            if not issue_number:
                if not repo.isnumeric():
                    await ctx.error(ctx.l.issue.stored_no_number)
                    return
                num: str = repo
                stored: Optional[str] = await self.bot.mgr.db.users.getitem(ctx, 'repo')
                if stored:
                    repo: str = stored
                    issue_number: str = num
                else:
                    await ctx.error(ctx.l.generic.nonexistent.repo.qa)
                    return

            try:
                issue: dict | str = await self.bot.github.get_issue(repo, int(issue_number))
            except ValueError:
                await ctx.error(ctx.l.issue.second_argument_number)
                return
            if isinstance(issue, str):
                if issue == 'repo':
                    await ctx.error(ctx.l.generic.nonexistent.repo.base)
                else:
                    await ctx.error(ctx.l.generic.nonexistent.issue_number)
                return

        em: str = '<:issue_open:788517560164810772>'
        if issue['state'].lower() == 'closed':
            em: str = '<:issue_closed:788517938168594452>'
        embed: discord.Embed = discord.Embed(
            color=self.bot.mgr.c.rounded,
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
                            self.bot.mgr.to_github_hyperlink(issue['author']['login']),
                            self.bot.mgr.github_to_discord_timestamp(issue['createdAt']))
        closed: str = '\n'
        if issue['closed']:
            closed: str = '\n' + ctx.fmt('closed_at', self.bot.mgr.github_to_discord_timestamp(issue['closedAt'])) + '\n'
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


async def setup(bot: GitBot) -> None:
    await bot.add_cog(Issue(bot))
