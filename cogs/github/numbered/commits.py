import discord
from typing import Optional, Literal
from discord.ext import commands
from lib.structs import GitBotEmbed, ParsedRepositoryData, GitBotCommandState, GitBot
from lib.utils.decorators import gitbot_command, normalize_repository
from lib.typehints import GitHubRepository
from lib.utils.regex import GIT_OBJECT_ID_RE, REPOSITORY_NAME_RE
from lib.structs.discord.context import GitBotContext


class Commits(commands.Cog):
    def __init__(self, bot: GitBot):
        self.bot: GitBot = bot

    @gitbot_command('commits')
    @commands.cooldown(5, 40, commands.BucketType.user)
    @normalize_repository
    async def commits_command(self, ctx: GitBotContext, repo: Optional[GitHubRepository] = None):
        _re_result = False
        maybe_ref = ''
        if repo and not (_re_result := REPOSITORY_NAME_RE.match(repo)):
            maybe_ref: str = repo
        if not repo or not _re_result:
            repo: Optional[str] = await self.bot.mgr.db.users.getitem(ctx, 'repo')
            if not repo:
                await self.bot.mgr.db.users.delitem(ctx, 'repo')
                await ctx.error(ctx.l.generic.nonexistent.repo.qa)
                return

        parsed: ParsedRepositoryData = self.bot.mgr.parse_repo(repo)
        if maybe_ref and not parsed.branch:
            parsed.branch = maybe_ref
        commits: list[dict] = await self.bot.github.get_latest_commits(parsed.slashname, parsed.branch)
        if isinstance(commits, str):
            if commits == 'ref':
                return await ctx.error(ctx.fmt('generic nonexistent ref', f'`{parsed.branch}`', f'`{parsed.slashname}`'))
            return await ctx.error(ctx.l.generic.nonexistent.repo.base)
        if not commits:
            return await ctx.error(ctx.l.commits.empty)
        embed: GitBotEmbed = GitBotEmbed(
            title=self.bot.mgr.e.github + '  ' + ctx.fmt('commits embed title',
                                                f'`{parsed.slashname}{f"/{parsed.branch}" if parsed.branch else ""}`'),
            description=self.bot.mgr.option_display_list_format([f'[`{c["abbreviatedOid"]}`]({c["url"]}) '
                                                        f'{self.bot.mgr.truncate(c["messageHeadline"], 53)}' for c in commits]),
            url=(f'https://github.com/{parsed.slashname}/commits' if not parsed.branch
                 else f'https://github.com/{parsed.slashname}/commits/{parsed.branch}'),
            footer=ctx.l.commits.embed.footer
        )

        async def _callback(_, res: discord.Message) -> GitBotCommandState:
            if res.content.lower() in ('cancel', 'quit', 'exit'):
                return GitBotCommandState.FAILURE
            if oid_matched := self.bot.mgr.get_by_key_from_sequence(commits, 'abbreviatedOid', res.content):
                ctx.data = oid_matched
                return GitBotCommandState.SUCCESS
            elif numbers := self.bot.mgr.get_numbers_in_range_in_str(res.content, len(commits)):
                ctx.data = commits[numbers[0]-1 if numbers[0] != 0 else 0]
                return GitBotCommandState.SUCCESS
            await ctx.error(ctx.l.commits.no_match)
            return GitBotCommandState.CONTINUE

        await embed.input_with_timeout(ctx=ctx, event='message', timeout=30,
                                       response_callback=_callback)
        if ctx.data:
            await ctx.invoke(self.commit_command, repo=None, oid=None)

    @gitbot_command('commit')
    @commands.cooldown(5, 40, commands.BucketType.user)
    @normalize_repository
    async def commit_command(self,
                             ctx: GitBotContext,
                             repo: Optional[GitHubRepository] = None,
                             oid: Optional[str] = None):
        ctx.fmt.set_prefix('commit')
        is_stored: bool = False
        if oid and oid.lower() in ('last', 'latest', 'newest', 'recent'):
            oid = None
        if not ctx.data:
            if repo and not oid and GIT_OBJECT_ID_RE.match(repo):
                oid: str = repo
                repo = None
                self.bot.mgr.debug(f'oid "{oid}" matched in place of the repo param, switching arguments')
            if not repo:
                repo: Optional[str] = await self.bot.mgr.db.users.getitem(ctx, 'repo')
                if not repo:
                    await self.bot.mgr.db.users.delitem(ctx, 'repo')
                    await ctx.error(ctx.l.generic.nonexistent.repo.qa)
                    return
                is_stored: bool = True
            commit: Optional[dict] | Literal[False] = (await self.bot.github.get_latest_commit(repo) if not oid
                                                       else await self.bot.github.get_commit(repo, oid))
        else:
            commit: dict = ctx.data
        if not commit:
            if commit is False:
                if is_stored and oid:
                    await ctx.error(await ctx.error(ctx.l.generic.nonexistent.repo.qa_changed))
                    await self.bot.mgr.db.users.delitem(ctx, 'repo')
                else:
                    await ctx.error(ctx.l.generic.nonexistent.repo.base)
            else:
                await ctx.error(ctx.fmt('!generic nonexistent commit', f'`{repo.lower()}`'))
        else:
            truncated_headline: str = self.bot.mgr.truncate(commit['messageHeadline'], 43)
            # 56 because we want the icon, thumbnail, headline, and the abbreviated object ID
            # to fit on the same title line in the fully expanded Discord client chat box
            embed: GitBotEmbed = GitBotEmbed(
                title=f'{self.bot.mgr.e.branch}  {truncated_headline} `{commit["abbreviatedOid"]}`',
                url=commit['url'],
                footer=ctx.l.commit.footer_latest if is_stored and not oid else None
            )
            if commit['author']['user'] and commit['author']['user'].get('avatarUrl'):
                embed.set_thumbnail(url=commit['author']['user']['avatarUrl'])
            full_headline: str = (commit['messageHeadline'] + '\n\n'
                                  if len(truncated_headline) < len(commit['messageHeadline']) else '')
            message: str = (f"{self.bot.mgr.truncate(commit['messageBody'], 247, full_word=True)}"
                            if commit['messageBody'] and commit['messageBody'] != commit['messageHeadline']
                            else '')
            empty: str = ctx.l.commit.fields.message.empty if not full_headline and not message else ''
            message: str = '```' + full_headline + message + empty + '```'
            embed.add_field(name=f':notepad_spiral: {ctx.l.commit.fields.message.name}:', value=message)
            commit_time: str = ctx.fmt('fields info pushed_at' if commit['pushedDate'] else 'fields info committed_at',
                                       self.bot.mgr.to_github_hyperlink(commit['author']['user']['login']),
                                       self.bot.mgr.github_to_discord_timestamp(commit['pushedDate'] if commit['pushedDate']
                                                                       else commit['committedDate'])) + '\n'
            signature: str = ''
            if sig := commit['signature']:
                if sig['isValid']:
                    if sig['signer'] and not sig['wasSignedByGitHub']:
                        signature: str = ctx.fmt('fields info signature valid user',
                                                 self.bot.mgr.to_github_hyperlink(sig['signer']['login'])) + '\n'
                    else:
                        signature: str = ctx.fmt('fields info signature valid github') + '\n'
                else:
                    signature: str = ctx.l.commit.fields.info.signature.invalid + '\n'
            committed_via_web: str = (ctx.l.commit.fields.info.committed_via_web + '\n' if
                                      commit['committedViaWeb'] else '')
            changes: str = self.bot.mgr.populate_generic_numbered_resource(ctx.l.commit.fields.changes,
                                                                           '```diff\n{files}\n+ '
                                                                           '{additions}\n- {deletions}```',
                                                                           files=commit['changedFiles'],
                                                                           additions=commit['additions'],
                                                                           deletions=commit['deletions'])
            checks: str = ''
            if commit['checkSuites']:
                ctx.fmt.set_prefix('commit fields info checks')
                completed: int = len(self.bot.mgr.get_by_key_from_sequence(suites := commit['checkSuites']['nodes'],
                                                                  'status', 'COMPLETED', multiple=True))
                queued: int = len(self.bot.mgr.get_by_key_from_sequence(suites, 'status', 'QUEUED', multiple=True))
                in_progress: int = len(self.bot.mgr.get_by_key_from_sequence(suites, 'status', 'IN_PROGRESS', multiple=True))
                checks: str = self.bot.mgr.populate_generic_numbered_resource(ctx.l.commit.fields.info.checks,
                                                                              '{completed}, {queued}; {in_progress}',
                                                                              completed=completed,
                                                                              queued=queued,
                                                                              in_progress=in_progress)
            info: str = f'{commit_time}{signature}{committed_via_web}{checks}'
            embed.add_field(name=f':mag_right: {ctx.l.commit.fields.info.name}:', value=info)
            embed.add_field(name=f':gear: {ctx.l.commit.fields.changes.name}:', value=changes)
            embed.add_field(name=f':label: {ctx.l.commit.fields.oid}:', value=f'```\n{commit["oid"]}```')
            await ctx.send(embed=embed, view_on_url=commit['url'])


async def setup(bot: GitBot) -> None:
    await bot.add_cog(Commits(bot))
