import os
import os.path
import json
import aiofiles
import shutil
import subprocess
from discord.ext import commands
from typing import Optional
from lib.structs import GitBotEmbed
from lib.globs import Git, Mgr
from lib.utils.decorators import gitbot_command
from lib.typehints import GitHubRepository

_25MB_BYTES: int = int(25 * (1024 ** 2))


class LinesOfCode(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot

    @gitbot_command(name='loc-nocache', aliases=['loc-no-cache'])
    @commands.cooldown(3, 60, commands.BucketType.user)
    @commands.max_concurrency(10)
    async def lines_of_code_command_nocache(self, ctx: commands.Context, repo: GitHubRepository) -> None:
        ctx.__nocache__ = True
        await ctx.invoke(self.lines_of_code_command, repo=repo)

    @gitbot_command(name='loc')
    @commands.cooldown(3, 60, commands.BucketType.user)
    @commands.max_concurrency(10)
    async def lines_of_code_command(self, ctx: commands.Context, repo: GitHubRepository) -> None:
        ctx.fmt.set_prefix('loc')
        r: Optional[dict] = await Git.get_repo(repo)
        if not r:
            await ctx.err(ctx.l.generic.nonexistent.repo.base)
            return
        processed: Optional[dict] = await self.process_repo(ctx, repo)
        if not processed:
            await ctx.err(ctx.l.loc.file_too_big)
            return
        title: str = ctx.fmt('title', repo)
        embed: GitBotEmbed = GitBotEmbed(
            color=0x00a6ff,
            title=title,
            url=r['url'],
            description=(ctx.fmt('description', processed["header"]["n_lines"], processed["SUM"]["nFiles"])
                         + '\n'
                         + f'{"⎯" * len(title)}\n'
                         + f'**{ctx.l.loc.stats.code}:** {processed["SUM"]["code"]}\n'
                         + f'**{ctx.l.loc.stats.blank}:** {processed["SUM"]["blank"]}\n'
                         + f'**{ctx.l.loc.stats.comments}:** {processed["SUM"]["comment"]}\n'
                         + f'**{ctx.l.loc.stats.detailed}:**\n'
                         + await self.prepare_result_sheet(processed)),
            footer=ctx.l.loc.footer
        )
        await ctx.send(embed=embed)

    async def process_repo(self, ctx: commands.Context, repo: GitHubRepository) -> Optional[dict]:
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
            output: dict = json.loads(subprocess.check_output(['/bin/perl', 'cloc.pl', '--json', tmp_dir_path]))
        except subprocess.CalledProcessError:
            pass
        else:
            Mgr.loc_cache[repo] = output
            return output
        finally:
            try:
                shutil.rmtree(tmp_dir_path)
                os.remove(tmp_zip_path)
            except FileNotFoundError:
                pass

    async def prepare_result_sheet(self, data: dict) -> str:
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
