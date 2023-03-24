import discord
from typing import Optional
from lib.typehints import GitHubRepository
from discord.ext import commands
from lib.utils.decorators import normalize_repository, gitbot_command
from lib.structs.discord.context import GitBotContext
from lib.structs.discord.bot import GitBot


class PullRequest(commands.Cog):
    def __init__(self, bot: GitBot):
        self.bot: GitBot = bot
        self.pr_states: dict = {
            'open': self.bot.mgr.e.pr_open,
            'closed': self.bot.mgr.e.pr_closed,
            'merged': self.bot.mgr.e.pr_merged
        }

    @gitbot_command(name='pr', aliases=['pull', 'pull-request', 'pullrequest'])
    @commands.cooldown(10, 30, commands.BucketType.user)
    @normalize_repository
    async def pull_request_command(self,
                                   ctx: GitBotContext,
                                   repo: GitHubRepository,
                                   pr_number: Optional[str] = None):
        ctx.fmt.set_prefix('pr')
        if ctx.data:
            pr: dict = getattr(ctx, 'data')
            pr_number: str | int = pr['number']
        else:
            if not pr_number:
                if not repo.isnumeric():
                    await ctx.error(ctx.l.pr.stored_no_number)
                    return
                elif not pr_number and repo.isnumeric():
                    num: str = repo
                    stored: Optional[str] = await self.bot.mgr.db.users.getitem(ctx, 'repo')
                    if stored:
                        repo: str = stored
                        pr_number: str = num
                    else:
                        await ctx.error(ctx.l.generic.nonexistent.repo.qa)
                        return

            if pr_number[0] == '#':
                pr_number = pr_number[1:]

            try:
                pr: dict | str = await self.bot.github.get_pull_request(repo, int(pr_number))
            except ValueError:
                await ctx.error(ctx.l.pr.second_argument_number)
                return

            if isinstance(pr, str):
                if pr == 'repo':
                    await ctx.error(ctx.l.generic.nonexistent.repo.base)
                else:
                    await ctx.error(ctx.l.generic.nonexistent.pr_number)
                return

        title: str = self.bot.mgr.truncate(pr['title'], 90)
        embed: discord.Embed = discord.Embed(
                title=f"{self.pr_states[pr['state'].lower()]}  {title} #{pr_number}",
                url=pr['url'],
                color=self.bot.mgr.c.rounded,
        )
        embed.set_thumbnail(url=pr['author']['avatarUrl'])
        if all(['bodyText' in pr and pr['bodyText'], len(pr['bodyText'])]):
            embed.add_field(name=':notepad_spiral: Body:',
                            value=f"```{self.bot.mgr.truncate(pr['bodyText'], 387, full_word=True)}```",
                            inline=False)
        user: str = ctx.fmt('created_at',
                            self.bot.mgr.to_github_hyperlink(pr['author']['login']),
                            self.bot.mgr.github_to_discord_timestamp(pr['createdAt']))
        if pr['closed']:
            closed: str = '\n' + ctx.fmt('closed_at', self.bot.mgr.github_to_discord_timestamp(pr['closedAt'])) + '\n'
        else:
            closed: str = '\n'
        comments_and_reviews: str = self.bot.mgr.populate_generic_numbered_resource(ctx.l.pr,
                                                                                    '{comments} {linking_word_1}'
                                                                                    ' {reviews}\n',
                                                                                    comments=pr['comments'][
                                                                                        'totalCount'],
                                                                                    reviews=pr['reviews']['totalCount'])
        commit_c: int = int(pr["commits"]["totalCount"])
        commits = f'[{ctx.fmt("commits plural", commit_c)}]({pr["url"]}/commits)'
        if commit_c == 1:
            commits = f'[{ctx.l.pr.commits.singular}]({pr["url"]}/commits)'
        files_changed: str = f'{ctx.fmt("files plural", pr["changedFiles"], pr["url"] + "/files")} {ctx.l.pr.linking_word_2} {commits}\n'
        if pr["changedFiles"] == 1:
            files_changed: str = f'{ctx.fmt("files singular", pr["url"] + "/files")} {ctx.l.pr.linking_word_2} {commits}\n'
        additions_and_deletions: str = self.bot.mgr.populate_generic_numbered_resource(ctx.l.pr,
                                                                                       '{additions} {linking_word_3}'
                                                                                       ' {deletions}\n',
                                                                                       additions=pr['additions'],
                                                                                       deletions=pr['deletions'])
        assignee_strings = [f"- [{u[0]}]({u[1]})\n" for u in pr['assignees']['users']]
        reviewer_strings = [f"- [{u[0]}]({u[1]})\n" for u in pr['reviewers']['users']]
        participant_strings = [f"- [{u[0]}]({u[1]})\n" for u in pr['participants']['users']]

        def _extend(_list: list, item: str) -> list:
            _list.extend(item)
            return _list

        assignee_strings: list = (assignee_strings if len(assignee_strings) <= 3 else
                                  _extend(assignee_strings[:3], ctx.fmt('more_items', len(assignee_strings) - 3)))
        reviewer_strings: list = (reviewer_strings if len(reviewer_strings) <= 3 else
                                  _extend(reviewer_strings[:3], ctx.fmt('more_items', len(reviewer_strings) - 3)))
        participant_strings: list = (participant_strings if len(participant_strings) <= 3 else
                                     _extend(participant_strings[:3],
                                             ctx.fmt('more_items', len(participant_strings) - 3)))
        cross_repo: str = ctx.l.pr.fork if pr['isCrossRepository'] else ''
        info: str = f'{user}{closed}{comments_and_reviews}{files_changed}{additions_and_deletions}{cross_repo}'
        embed.add_field(name=f':mag_right: {ctx.l.pr.glossary[0]}:', value=info, inline=False)

        embed.add_field(name=f'{ctx.l.pr.glossary[1]}:',
                        value=''.join(participant_strings) if participant_strings else ctx.l.pr.no_participants)
        embed.add_field(name=f'{ctx.l.pr.glossary[2]}:',
                        value=''.join(assignee_strings) if assignee_strings else ctx.l.pr.no_assignees)
        embed.add_field(name=f'{ctx.l.pr.glossary[3]}:',
                        value=''.join(reviewer_strings) if reviewer_strings else ctx.l.pr.no_reviewers)
        if pr['labels']:
            embed.add_field(name=f':label: {ctx.l.pr.glossary[4]}:', value=' '.join([f"`{lb}`" for lb in pr['labels']]),
                            inline=False)

        await ctx.send(embed=embed, view_on_url=pr['url'])


async def setup(bot: GitBot) -> None:
    await bot.add_cog(PullRequest(bot))
