import re
import discord
from .snippet_tools import handle_url, gen_carbon_inmemory
from aiohttp import ClientSession
from discord.ext import commands
from lib.utils import regex
from lib.globs import Mgr

RAW_CODEBLOCK_LEN_THRESHOLD: int = 25
CARBON_LEN_THRESHOLD: int = 50


class Snippets(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot
        self.ses: ClientSession = ClientSession(loop=self.bot.loop)

    @commands.group(name='snippet', aliases=['-snippet', '--snippet'], invoke_without_command=True)
    @commands.cooldown(10, 30, commands.BucketType.user)
    async def snippet_command_group(self, ctx: commands.Context, *, link_or_codeblock: str) -> None:
        ctx.fmt.set_prefix('snippets')
        if ctx.invoked_subcommand is None:
            is_codeblock: bool = bool(re.findall(regex.CODEBLOCK_RE, link_or_codeblock))
            if is_codeblock:
                if len(link_or_codeblock.splitlines()) > CARBON_LEN_THRESHOLD:
                    await ctx.err(ctx.fmt('length_limit_exceeded', CARBON_LEN_THRESHOLD))
                    return
                msg: discord.Message = await ctx.send(f'{Mgr.e.github}  Generating Carbon image...')
                await ctx.send(
                    file=discord.File(filename='snippet.png', fp=await gen_carbon_inmemory(link_or_codeblock)))
                await msg.delete()
            else:
                msg: discord.Message = await ctx.send(f'{Mgr.e.github}  Generating Carbon image...')
                text, err = await handle_url(ctx, link_or_codeblock,
                                             max_line_count=CARBON_LEN_THRESHOLD, wrap_in_codeblock=False)
                img = await gen_carbon_inmemory(text)
                await msg.delete()
                if text:
                    await ctx.send(
                        file=discord.File(filename='snippet.png', fp=img))
                else:
                    await ctx.err(err)

    @snippet_command_group.command(name='--raw', aliases=['-raw', 'raw'])
    @commands.cooldown(10, 30, commands.BucketType.user)
    async def raw_snippet_command(self, ctx: commands.Context, link: str) -> None:
        ctx.fmt.set_prefix('snippets')
        text, err = await handle_url(ctx, link)
        if text:
            await ctx.send(text)
        else:
            await ctx.err(err)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Snippets(bot))
