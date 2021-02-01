import discord
import datetime
from typing import Optional
from core.bot_config import Git
from discord.ext import commands


class Issue(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot
        self.emoji: str = '<:github:772040411954937876>'
        self.e: str = "<:ge:767823523573923890>"

    @commands.command(name='issue', aliases=['-issue', 'i'])
    @commands.cooldown(10, 30, commands.BucketType.user)
    async def issue_command(self, ctx: commands.Context, repo: str, issue_number: str = None) -> None:
        if hasattr(ctx, 'data'):
            issue: dict = getattr(ctx, 'data')
        else:
            if not issue_number and not repo.isnumeric():
                await ctx.send(
                    f'{self.e}  If you want to access the stored repo\'s PRs, please pass in a **pull request number!**')
                return
            elif not issue_number and repo.isnumeric():
                num = repo
                stored = await self.bot.get_cog('Config').getitem(ctx, 'repo')
                if stored:
                    repo = stored
                    issue_number = num
                else:
                    await ctx.send(
                        f'{self.e}  You don\'t have a quick access repo stored! **Type** `git config` **to do it.**')
                    return

            try:
                issue = await Git.get_issue(repo, int(issue_number))
            except ValueError:
                await ctx.send(f"{self.e}  The second argument must be an issue **number!**")
                return
            if isinstance(issue, str):
                if issue == 'repo':
                    await ctx.send(f"{self.e}  This repository **doesn't exist!**")
                else:
                    await ctx.send(f"{self.e}  An issue with this number **doesn't exist!**")
                return

        em: str = f"<:issue_open:788517560164810772>"
        if issue['state'].lower() == 'closed':
            em: str = '<:issue_closed:788517938168594452>'
        embed: discord.Embed = discord.Embed(
            color=0xefefef,
            title=f"{em}  {issue['title']} #{issue_number}",
            description=None,
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
            embed.add_field(name=':notepad_spiral: Body:', value=f"```{body}```", inline=False)

        created_at: datetime = datetime.datetime.strptime(issue['createdAt'], '%Y-%m-%dT%H:%M:%SZ')

        user: str = f"Created by [{issue['author']['login']}]({issue['author']['url']}) \
         on {created_at.strftime('%e, %b %Y')}"

        if issue['closed']:
            closed_at: datetime = datetime.datetime.strptime(issue['closedAt'], '%Y-%m-%dT%H:%M:%SZ')
            closed: str = f"\nClosed on {closed_at.strftime('%e, %b %Y')}\n"
        else:
            closed: str = '\n'

        assignees: str = f"{issue['assigneeCount']} assignees"
        if issue['assigneeCount'] == 1:
            assignees: str = 'one assignee'
        elif issue['assigneeCount'] == 0:
            assignees: str = 'no assignees'

        comments: str = f"Has {issue['commentCount']} comments"
        if issue['commentCount'] == 1:
            comments: str = "Has only one comment"
        elif issue['commentCount'] == 0:
            comments: str = "Has no comments"

        comments_and_assignees: str = f"{comments} and {assignees}"

        participants: str = f"\n{issue['participantCount']} people have participated in this issue" if \
            issue['participantCount'] != 1 else "\nOne person has participated in this issue"

        info: str = f"{user}{closed}{comments_and_assignees}{participants}"

        embed.add_field(name=':mag_right: Info:', value=info, inline=False)

        if issue['labels']:
            embed.add_field(name=':label: Labels:', value=' '.join([f"`{lb}`" for lb in issue['labels']]))

        embed.set_thumbnail(url=issue['author']['avatarUrl'])
        await ctx.send(embed=embed)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Issue(bot))
