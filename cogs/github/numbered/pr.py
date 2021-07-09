import discord
import datetime
from typing import Optional, Union
from lib.globs import Git, Mgr
from babel.dates import format_date
from discord.ext import commands
from lib.utils.decorators import normalize_repository

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
    @normalize_repository
    async def pull_request_command(self, ctx: commands.Context, repo: str, pr_number: Optional[str] = None):
        ctx.fmt.set_prefix('pr')
        if hasattr(ctx, 'data'):
            pr: dict = getattr(ctx, 'data')
            pr_number: Union[str, int] = pr['number']
        else:
            if not pr_number:
                if not repo.isnumeric():
                    await ctx.err(ctx.l.pr.stored_no_number)
                elif not pr_number and repo.isnumeric():
                    num: str = repo
                    stored: Optional[str] = await Mgr.db.users.getitem(ctx, 'repo')
                    if stored:
                        repo: str = stored
                        pr_number: str = num
                    else:
                        await ctx.err(ctx.l.generic.nonexistent.repo.qa)
                return

            try:
                pr: Union[dict, str] = await Git.get_pull_request(repo, int(pr_number))
            except ValueError:
                await ctx.err(ctx.l.pr.second_argument_number)
                return

            if isinstance(pr, str):
                if pr == 'repo':
                    await ctx.err(ctx.l.generic.nonexistent.repo.base)
                else:
                    await ctx.err(ctx.l.generic.nonexistent.pr_number)
                return

        title: str = pr['title'] if len(pr['title']) <= 90 else f"{pr['title'][:87]}..."
        embed: discord.Embed = discord.Embed(
            title=f"{PR_STATES[pr['state'].lower()]}  {title} #{pr_number}",
            url=pr['url'],
            color=0xefefef,
        )
        embed.set_thumbnail(url=pr['author']['avatarUrl'])
        if all(['bodyText' in pr and pr['bodyText'], len(pr['bodyText'])]):
            body = pr['bodyText']
            if len(body) > 390:
                body: str = body[:387]
                body: str = f"{body[:body.rindex(' ')]}...".strip()
            embed.add_field(name=':notepad_spiral: Body:', value=f"```{body}```", inline=False)

        user: str = ctx.fmt('created_at',
                            f"[{pr['author']['login']}]({pr['author']['url']})",
                            format_date(datetime.datetime.strptime(pr['createdAt'],
                                                                   '%Y-%m-%dT%H:%M:%SZ').date(),
                                        'full',
                                        locale=ctx.l.meta.name))

        if pr['closed']:
            closed: str = '\n' + ctx.fmt('closed_at', format_date(datetime.datetime.strptime(pr['closedAt'],
                                                                                             '%Y-%m-%dT%H:%M:%SZ').date(),
                                                                  'full',
                                                                  locale=ctx.l.meta.name)) + '\n'
        else:
            closed: str = '\n'

        reviews: str = ctx.fmt('reviews plural', pr['reviews']['totalCount'])
        if pr['reviews']['totalCount'] == 1:
            reviews: str = ctx.l.pr.reviews.singular
        elif pr['reviews']['totalCount'] == 0:
            reviews: str = ctx.l.pr.reviews.no_reviews

        comments: str = ctx.fmt('comments plural', pr['comments']['totalCount'])
        if pr['comments']['totalCount'] == 1:
            comments: str = ctx.l.pr.comments.singular
        elif pr['comments']['totalCount'] == 0:
            comments: str = ctx.l.pr.comments.no_comments

        comments_and_reviews: str = f'{comments} {ctx.l.pr.linking_word_1} {reviews}\n'

        commit_c: int = int(pr["commits"]["totalCount"])
        commits = f'[{ctx.fmt("commits plural", commit_c)}]({pr["url"]}/commits)'
        if commit_c == 1:
            commits = f'[{ctx.l.pr.commits.singular}]({pr["url"]}/commits)'
        files_changed: str = f'{ctx.fmt("files plural", pr["changedFiles"], pr["url"] + "/files")} {ctx.l.pr.linking_word_2} {commits}\n'
        if pr["changedFiles"] == 1:
            files_changed: str = f'{ctx.fmt("files singular", pr["url"] + "/files")} {ctx.l.pr.linking_word_2} {commits}\n'

        additions: str = ctx.fmt('additions plural', pr["additions"])
        if pr["additions"] == 1:
            additions: str = ctx.l.pr.additions.singular
        elif pr['additions'] == 0:
            additions: str = ctx.l.pr.additions.no_additions

        deletions: str = ctx.fmt('deletions plural', pr["deletions"])
        if pr['deletions'] == 1:
            deletions: str = ctx.l.pr.deletions.singular
        elif pr['deletions'] == 0:
            deletions: str = ctx.l.pr.deletions.no_deletions

        additions_and_deletions: str = f'{additions} {ctx.l.pr.linking_word_3} {deletions}\n'

        assignee_strings = [f"- [{u[0]}]({u[1]})\n" for u in pr['assignees']['users']]
        reviewer_strings = [f"- [{u[0]}]({u[1]})\n" for u in pr['reviewers']['users']]
        participant_strings = [f"- [{u[0]}]({u[1]})\n" for u in pr['participants']['users']]

        def _extend(_list: list, item: str) -> list:
            _list.extend(item)
            return _list

        assignee_strings = assignee_strings if len(assignee_strings) <= 3 else _extend(assignee_strings[:3], ctx.fmt('more_items', len(assignee_strings) - 3))
        reviewer_strings = reviewer_strings if len(reviewer_strings) <= 3 else _extend(reviewer_strings[:3], ctx.fmt('more_items', len(reviewer_strings) - 3))
        participant_strings = participant_strings if len(participant_strings) <= 3 else _extend(participant_strings[:3], ctx.fmt('more_items', len(participant_strings) - 3))

        cross_repo: str = ctx.l.pr.fork if pr['isCrossRepository'] else ''
        info: str = f'{user}{closed}{comments_and_reviews}{files_changed}{additions_and_deletions}{cross_repo}'
        embed.add_field(name=f':mag_right: {ctx.l.pr.glossary[0]}:', value=info, inline=False)

        embed.add_field(name=f'{ctx.l.pr.glossary[1]}:',
                        value=''.join(participant_strings) if participant_strings else ctx.l.pr.no_participants,
                        inline=True)
        embed.add_field(name=f'{ctx.l.pr.glossary[2]}:',
                        value=''.join(assignee_strings) if assignee_strings else ctx.l.pr.no_assignees,
                        inline=True)
        embed.add_field(name=f'{ctx.l.pr.glossary[3]}:',
                        value=''.join(reviewer_strings) if reviewer_strings else ctx.l.pr.no_reviewers,
                        inline=True)

        if pr['labels']:
            embed.add_field(name=f':label: {ctx.l.pr.glossary[4]}:', value=' '.join([f"`{lb}`" for lb in pr['labels']]), inline=False)

        await ctx.send(embed=embed)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(PullRequest(bot))
