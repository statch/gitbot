import os
import os.path
import json
import aiofiles
import shutil
import fnmatch
import subprocess
from discord.ext import commands
from typing import Optional
from lib.structs import GitBotEmbed
from lib.globs import Git, Mgr
from lib.utils.decorators import gitbot_command
from lib.typehints import GitHubRepository
from lib.structs.discord.context import GitBotContext

_25MB_BYTES: int = int(25 * (1024 ** 2))


class LinesOfCode(commands.Cog):
    # I know that using "perl" alone is insecure, but it will only be used in Windows dev environments
    __perl_command_line__: str = '/bin/perl' if os.name != 'nt' else 'perl'

    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot

    @gitbot_command(name='loc-nocache', aliases=['loc-no-cache'], hidden=True)
    @commands.cooldown(3, 60, commands.BucketType.user)
    @commands.max_concurrency(10)
    async def lines_of_code_command_nocache(self, ctx: GitBotContext, repo: GitHubRepository) -> None:
        ctx.__nocache__ = True
        await ctx.invoke(self.lines_of_code_command, repo=repo)

    @gitbot_command(name='loc')
    @commands.cooldown(3, 60, commands.BucketType.user)
    @commands.max_concurrency(10)
    async def lines_of_code_command(self, ctx: GitBotContext, repo: GitHubRepository) -> None:
        ctx.fmt.set_prefix('loc')
        r: Optional[dict] = await Git.get_repo(repo)
        if not r:
            await ctx.error(ctx.l.generic.nonexistent.repo.base)
            return
        processed: Optional[tuple[dict, int | None]] | dict = await self.process_repo(ctx, repo)
        if not processed:
            await ctx.error(ctx.l.loc.file_too_big)
            return
        title: str = ctx.fmt('title', f'`{repo}`')
        if isinstance(processed, dict):
            count: int = 0
        else:
            count: int = processed[1]
            processed = processed[0]
        processed: dict
        embed: GitBotEmbed = GitBotEmbed(
            color=0x00a6ff,
            title=title,
            url=r['url'],
            description=(ctx.fmt('description', processed['header']['n_lines'], processed['SUM']['nFiles'])
                         + '\n'
                         + f'{"⎯" * len(title)}\n'
                         + f'**{ctx.l.loc.stats.code}:** {processed["SUM"]["code"]}\n'
                         + f'**{ctx.l.loc.stats.blank}:** {processed["SUM"]["blank"]}\n'
                         + f'**{ctx.l.loc.stats.comments}:** {processed["SUM"]["comment"]}\n'
                         + f'**{ctx.l.loc.stats.detailed}:**\n'
                         + await self.prepare_result_sheet(processed)),
            footer=ctx.l.loc.footer.credit if not count
            else (ctx.fmt('footer with_count plural', count) if count > 1 else ctx.fmt('footer with_count singular')),
        )
        await ctx.reply(embed=embed, mention_author=False)

    @staticmethod
    def remove_matches(directory: str, pattern: str) -> int:
        Mgr.debug(f'Removing files matching pattern "{pattern}" from directory "{directory}"')
        c_removed: int = 0
        for root, dirs, files in os.walk(directory):
            for f in files:
                if fnmatch.fnmatch(f, pattern):
                    Mgr.debug(f'Removing file "{f}"')
                    c_removed += 1
                    os.remove(os.path.join(root, f))
            for d in dirs:
                if fnmatch.fnmatch(d, pattern):
                    Mgr.debug(f'Removing directory "{d}"')
                    c_removed += 1
                    shutil.rmtree(os.path.join(root, d))
        Mgr.debug(f'Removed {c_removed} entries.')
        return c_removed

    @staticmethod
    async def process_repo(ctx: GitBotContext, repo: GitHubRepository) -> Optional[tuple[dict, int | None]]:
        if (not ctx.__nocache__) and (cached := Mgr.loc_cache.get(repo := repo.lower())):
            return cached
        tmp_zip_path: str = f'./tmp/{ctx.message.id}.zip'
        tmp_dir_path: str = tmp_zip_path[:-4]
        try:
            if not os.path.exists('./tmp'):
                os.mkdir('./tmp')
            files: Optional[bytes | bool] = await Git.get_repo_zip(repo, size_threshold=_25MB_BYTES)
            if not files:
                return None
            async with aiofiles.open(tmp_zip_path, 'wb') as fp:
                await fp.write(files)
            await Mgr.unzip_file(tmp_zip_path, tmp_dir_path)
            c_removed: int = 0
            cfg: dict | None = await Mgr.get_repo_gitbot_config(repo)
            if cfg and cfg.get('loc'):
                Mgr.debug(f'Found GitBot config for repo "{repo}"')
                if isinstance(cfg['loc'], dict) and (ignore := cfg['loc'].get('ignore')):
                    if isinstance(ignore, str):
                        ignore = [ignore]
                    for pattern in ignore:
                        c_removed += LinesOfCode.remove_matches(tmp_dir_path, pattern)
            output: dict = json.loads(subprocess.check_output([LinesOfCode.__perl_command_line__, 'cloc.pl',
                                                               '--json', tmp_dir_path]))
        except subprocess.CalledProcessError as e:
            Mgr.debug(f'the CLOC script failed with exit code {e.returncode}')
        else:
            Mgr.loc_cache[repo] = (output, c_removed)
            return output, c_removed
        finally:
            try:
                shutil.rmtree(tmp_dir_path)
                os.remove(tmp_zip_path)
            except FileNotFoundError:
                pass

    @staticmethod
    async def prepare_result_sheet(data: dict) -> str:
        result: str = '```py\n{}```'
        threshold: int = 15
        for k, v in data.items():
            if threshold == 0:
                break
            if k not in ('header', 'SUM'):
                result: str = result.format(f"{k}: {v['code']}\n{{}}")
                threshold -= 1
        result: str = result[:-5] + '```'
        return result


def setup(bot: commands.Bot) -> None:
    bot.add_cog(LinesOfCode(bot))
