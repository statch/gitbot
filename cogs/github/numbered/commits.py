from typing import Optional, Union, Literal
from discord.ext import commands
from lib.globs import Mgr, Git
from lib.structs import GitBotEmbed
from lib.utils.decorators import gitbot_command, normalize_repository
from lib.typehints import GitHubRepository
from lib.utils.regex import GIT_OBJECT_ID_RE


class Commits(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot

    @gitbot_command('commit')
    @commands.cooldown(5, 40, commands.BucketType.user)
    @normalize_repository
    async def commit_command(self,
                             ctx: commands.Context,
                             repo: Optional[GitHubRepository] = None,
                             oid: Optional[str] = None):
        # TODO add this to the help command
        ctx.fmt.set_prefix('commit')
        is_stored: bool = False
        if not hasattr(ctx, 'data'):
            if repo and not oid and GIT_OBJECT_ID_RE.match(repo):
                oid: str = repo
                repo = None
                Mgr.debug(f'oid "{oid}" matched in place of the repo param, switching arguments')
            if not repo:
                repo: Optional[str] = await Mgr.db.users.getitem(ctx, 'repo')
                if not repo:
                    await Mgr.db.users.delitem(ctx, 'repo')
                    await ctx.err(ctx.l.generic.nonexistent.repo.qa)
                    return
                is_stored: bool = True
            commit: Union[Optional[dict], Literal[False]] = (await Git.get_latest_commit(repo) if not oid
                                                             else await Git.get_commit(repo, oid))
        else:
            commit: dict = ctx.data
        if not commit:
            if commit is False:
                if is_stored:
                    await ctx.err(await ctx.err(ctx.l.generic.nonexistent.repo.qa_changed))
                else:
                    await ctx.err(ctx.l.generic.nonexistent.repo.base)
            else:
                await ctx.err(ctx.fmt('!generic nonexistent commit', f'`{repo.lower()}`'))
        else:
            truncated_headline: str = Mgr.truncate(commit['messageHeadline'], 43)
            # 56 because we want the icon, thumbnail, headline, and the abbreviated object ID
            # to fit on the same title line in the fully expanded Discord client chat box
            embed: GitBotEmbed = GitBotEmbed(
                title=f'{Mgr.e.branch}  {truncated_headline} `{commit["abbreviatedOid"]}`',
                url=commit['url'],
                thumbnail=commit['author']['user']['avatarUrl']
            )
            full_headline: str = (commit['messageHeadline'] + '\n\n'
                                  if len(truncated_headline) < len(commit['messageHeadline']) else '')
            message: str = (f"{Mgr.truncate(commit['messageBody'], 247, full_word=True)}"
                            if commit['messageBody'] and commit['messageBody'] != commit['messageHeadline']
                            else '')
            empty: str = ctx.l.commit.fields.message.empty if not full_headline and not message else ''
            message: str = '```' + full_headline + message + empty + '```'
            embed.add_field(name=f':notepad_spiral: {ctx.l.commit.fields.message.name}:', value=message)
            commit_time: str = ctx.fmt('fields info pushed_at' if commit['pushedDate'] else 'fields info committed_at',
                                       Mgr.to_github_hyperlink(commit['author']['user']['login']),
                                       Mgr.github_to_discord_timestamp(commit['pushedDate'] if commit['pushedDate']
                                                                       else commit['committedDate'])) + '\n'
            signature: str = ''
            if sig := commit['signature']:
                if sig['isValid']:
                    if sig['signer'] and not sig['wasSignedByGitHub']:
                        signature: str = ctx.fmt('fields info signature valid user',
                                                 Mgr.to_github_hyperlink(sig['signer']['login'])) + '\n'
                    else:
                        signature: str = ctx.fmt('fields info signature valid github') + '\n'
                else:
                    signature: str = ctx.l.commit.fields.info.signature.invalid + '\n'
            committed_via_web: str = (ctx.l.commit.fields.info.committed_via_web + '\n' if
                                      commit['committedViaWeb'] else '')
            changes: str = Mgr.populate_localized_generic_number_map(ctx.l.commit.fields.changes,
                                                                     '```diff\n{files}\n+ '
                                                                     '{additions}\n- {deletions}```',
                                                                     files=commit['changedFiles'],
                                                                     additions=commit['additions'],
                                                                     deletions=commit['deletions'])
            checks: str = ''
            if commit['checkSuites']:
                ctx.fmt.set_prefix('commit fields info checks')
                completed: int = len(Mgr.get_by_key_from_sequence(suites := commit['checkSuites']['nodes'],
                                                                  'status', 'COMPLETED', multiple=True))
                queued: int = len(Mgr.get_by_key_from_sequence(suites, 'status', 'QUEUED', multiple=True))
                in_progress: int = len(Mgr.get_by_key_from_sequence(suites, 'status', 'IN_PROGRESS', multiple=True))
                checks: str = Mgr.populate_localized_generic_number_map(ctx.l.commit.fields.info.checks,
                                                                        '{completed}, {queued}; {in_progress}',
                                                                        completed=completed,
                                                                        queued=queued,
                                                                        in_progress=in_progress)
            info: str = f'{commit_time}{signature}{committed_via_web}{checks}'
            embed.add_field(name=f':mag_right: {ctx.l.commit.fields.info.name}:', value=info, inline=False)
            embed.add_field(name=f':gear: {ctx.l.commit.fields.changes.name}:', value=changes, inline=False)
            embed.add_field(name=f':label: {ctx.l.commit.fields.oid}:', value=f'```\n{commit["oid"]}```', inline=False)
            await ctx.send(embed=embed)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Commits(bot))
