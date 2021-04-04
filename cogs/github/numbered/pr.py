import discord
import datetime
from typing import Optional
from core.globs import Git, Mgr
from discord.ext import commands

PR_STATES: dict = {
    "open": Mgr.e.pr_open,
    "closed": Mgr.e.pr_closed,
    "merged": Mgr.e.pr_merged
}


class PullRequest(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot

    @commands.command(name='pr', aliases=['pull', '-pr', '--pr', '--pullrequest', '-pull'])
    @commands.cooldown(10, 30, commands.BucketType.user)
    async def pull_request_command(self, ctx: commands.Context, repo: str, pr_number: Optional[str] = None):
        if hasattr(ctx, 'data'):
            pr: dict = getattr(ctx, 'data')
            pr_number: int = pr['number']
        else:
            if not pr_number:
                if not repo.isnumeric():
                    await ctx.send(
                        f'{Mgr.e.err}  If you want to access the stored repo\'s PRs, please pass in a **pull request number!**')
                    return
                elif not pr_number and repo.isnumeric():
                    num = repo
                    stored = await self.bot.get_cog('Config').getitem(ctx, 'repo')
                    if stored:
                        repo = stored
                        pr_number = num
                    else:
                        await ctx.send(
                            f'{Mgr.e.err}  You don\'t have a quick access repo stored! **Type** `git config` **to do it.**')
                        return

            try:
                pr: dict = await Git.get_pull_request(repo, int(pr_number))
            except ValueError:
                await ctx.send(f"{Mgr.e.err}  The second argument must be a pull request **number!**")
                return

            if isinstance(pr, str):
                if pr == 'repo':
                    await ctx.send(f"{Mgr.e.err}  This repository **doesn't exist!**")
                else:
                    await ctx.send(f"{Mgr.e.err}  A pull request with this number **doesn't exist!**")
                return

        title: str = pr['title'] if len(pr['title']) <= 90 else f"{pr['title'][:87]}..."
        state = pr['state'].lower().capitalize()
        embed: discord.Embed = discord.Embed(
            title=f"{PR_STATES[state.lower()]}  {title} #{pr_number}",
            url=pr['url'],
            color=0xefefef,
            description=None
        )
        embed.set_thumbnail(url=pr['author']['avatarUrl'])
        if all(['bodyText' in pr and pr['bodyText'], len(pr['bodyText'])]):
            body = pr['bodyText']
            if len(body) > 390:
                body: str = body[:387]
                body: str = f"{body[:body.rindex(' ')]}...".strip()
            embed.add_field(name=':notepad_spiral: Body:', value=f"```{body}```", inline=False)

        created_at: datetime = datetime.datetime.strptime(pr['createdAt'], '%Y-%m-%dT%H:%M:%SZ')
        user: str = f"Created by [{pr['author']['login']}]({pr['author']['url']}) on {created_at.strftime('%e, %b %Y')}"

        if pr['closed']:
            closed_at: datetime = datetime.datetime.strptime(pr['closedAt'], '%Y-%m-%dT%H:%M:%SZ')
            closed: str = f"\nClosed on {closed_at.strftime('%e, %b %Y')}\n"
        else:
            closed: str = '\n'

        reviews: str = f"{pr['reviews']['totalCount']} reviews"
        if pr['reviews']['totalCount'] == 1:
            reviews: str = 'one review'
        elif pr['reviews']['totalCount'] == 0:
            reviews: str = 'no reviews'

        comments: str = f"Has {pr['comments']['totalCount']} comments"
        if pr['comments']['totalCount'] == 1:
            comments: str = "Has only one comment"
        elif pr['comments']['totalCount'] == 0:
            comments: str = 'Has no comments'

        comments_and_reviews: str = f'{comments} and {reviews}\n'

        commit_c: int = pr["commits"]["totalCount"]
        commits = f'[{commit_c} commits]({pr["url"]}/commits)'
        if commit_c == 1:
            commits = f'[one commit]({pr["url"]}/commits)'

        files_changed: str = f'[{pr["changedFiles"]} files]({pr["url"]}/files) ' \
                             f'have been changed in {commits}\n'
        if pr["changedFiles"] == 1:
            files_changed: str = f'[One file]({pr["url"]}/files) was changed ' \
                                 f'in [{commit_c} commits]({pr["url"]}/commits)\n'
        elif pr['changedFiles'] == 0:
            files_changed: str = f'No files have been changed in this PR\n'

        additions: str = f'Updated with {pr["additions"]} additions'
        if pr["additions"] == 1:
            additions: str = 'Updated with one addition'
        elif pr['additions'] == 0:
            additions: str = 'Updated with no additions'

        deletions: str = f'{pr["deletions"]} deletions'
        if pr['deletions'] == 1:
            deletions: str = 'one deletion'
        elif pr['deletions'] == 0:
            deletions: str = 'no deletions'

        additions_and_deletions: str = f'{additions} and {deletions}.\n'

        assignee_strings = [f"- [{u[0]}]({u[1]})\n" for u in pr['assignees']['users']]
        reviewer_strings = [f"- [{u[0]}]({u[1]})\n" for u in pr['reviewers']['users']]
        participant_strings = [f"- [{u[0]}]({u[1]})\n" for u in pr['participants']['users']]

        assignee_strings = assignee_strings if len(assignee_strings) <= 3 else assignee_strings[
                                                                               :3] + f'- and {len(assignee_strings) - 3} more'

        reviewer_strings = reviewer_strings if len(reviewer_strings) <= 3 else reviewer_strings[
                                                                               :3] + f'- and {len(reviewer_strings) - 3} more'

        participant_strings = participant_strings if len(participant_strings) <= 3 else participant_strings[
                                                                                        :3] + f'- and {len(participant_strings)} more'

        cross_repo: str = f'This pull request came from a fork.' if pr['isCrossRepository'] else ''
        info: str = f'{user}{closed}{comments_and_reviews}{files_changed}{additions_and_deletions}{cross_repo}'
        embed.add_field(name=':mag_right: Info:', value=info, inline=False)

        embed.add_field(name='Participants:',
                        value=''.join(participant_strings) if participant_strings else f'No participants',
                        inline=True)
        embed.add_field(name='Assignees:',
                        value=''.join(assignee_strings) if assignee_strings else f'No assignees',
                        inline=True)
        embed.add_field(name='Reviewers:',
                        value=''.join(reviewer_strings) if reviewer_strings else f'No reviewers',
                        inline=True)

        if pr['labels']:
            embed.add_field(name=':label: Labels:', value=' '.join([f"`{lb}`" for lb in pr['labels']]), inline=False)

        await ctx.send(embed=embed)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(PullRequest(bot))
