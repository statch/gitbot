import os
import os.path
import json
import aiofiles
import shutil
import subprocess
import discord
from discord.ext import commands
from typing import Optional, Any, Union
from lib.globs import Git, Mgr


class LinesOfCode(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot

    @commands.command(name='loc', aliases=['-loc', '--loc'])
    @commands.cooldown(3, 60, commands.BucketType.user)
    @commands.max_concurrency(10)
    async def lines_of_code_command(self, ctx: commands.Context, repo: str) -> None:
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
        embed: discord.Embed = discord.Embed(
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
                         + await self.prepare_result_sheet(processed))
        )
        embed.set_footer(text=ctx.l.loc.footer)
        await ctx.send(embed=embed)

    async def process_repo(self, ctx: commands.Context, repo: str) -> Optional[dict]:
        tmp_zip_path: str = f'./tmp/{ctx.message.id}.zip'
        tmp_dir_path: str = tmp_zip_path[:-4]
        try:
            if not os.path.exists('./tmp'):
                os.mkdir('./tmp')
            files: Optional[Union[bytes, bool]] = await Git.get_repo_zip(repo)
            if not files:
                return None
            async with aiofiles.open(tmp_zip_path, 'wb') as fp:
                await fp.write(files)
            await Mgr.unzip_file(tmp_zip_path, tmp_dir_path)
            output: Any = subprocess.check_output(['perl', 'cloc.pl', '--json', tmp_dir_path])
            output: dict = json.loads(output)
        except subprocess.CalledProcessError:
            pass
        else:
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
