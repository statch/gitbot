import re
import discord
from .snippet_tools import handle_url, gen_carbon_inmemory  # noqa
from aiohttp import ClientSession
from discord.ext import commands
from lib.utils import regex
from lib.globs import Mgr
from typing import Optional
from lib.utils.decorators import gitbot_group
from lib.structs.discord.context import GitBotContext, MessageFormattingStyle


class Snippets(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot
        self.ses: ClientSession = ClientSession(loop=self.bot.loop)

    @gitbot_group(name='snippet', invoke_without_command=True)
    @commands.cooldown(3, 60, commands.BucketType.user)
    async def snippet_command_group(self, ctx: GitBotContext, *, link_or_codeblock: str) -> None:
        ctx.fmt.set_prefix('snippets')
        if ctx.invoked_subcommand is None:
            codeblock: Optional[str] = Mgr.extract_content_from_codeblock(link_or_codeblock)
            if codeblock:
                if len(codeblock.splitlines()) > Mgr.env.carbon_len_threshold:
                    await ctx.send(ctx.fmt('length_limit_exceeded', Mgr.env.carbon_len_threshold),
                                   style=MessageFormattingStyle.ERROR)
                    return
                msg: discord.Message = await ctx.send(ctx.l.snippets.generating, style=MessageFormattingStyle.INFO)

                await ctx.send(file=discord.File(filename='snippet.png', fp=await gen_carbon_inmemory(codeblock)))
                await msg.delete()
            elif bool(re.search(regex.GITHUB_LINES_URL_RE, link_or_codeblock) or
                      re.search(regex.GITLAB_LINES_URL_RE, link_or_codeblock)):
                msg: discord.Message = await ctx.send(ctx.l.snippets.generating, style=MessageFormattingStyle.INFO)
                text, err = await handle_url(ctx, link_or_codeblock,
                                             max_line_count=Mgr.env.carbon_len_threshold, wrap_in_codeblock=False)
                await msg.delete()
                if text:
                    await ctx.send(file=discord.File(filename='snippet.png', fp=await gen_carbon_inmemory(text)))
                else:
                    await ctx.send(err, style=MessageFormattingStyle.ERROR)
            else:
                await ctx.send(ctx.l.snippets.no_lines_mentioned, style=MessageFormattingStyle.ERROR)

    @snippet_command_group.command(name='raw')
    @commands.cooldown(3, 30, commands.BucketType.user)
    async def raw_snippet_command(self, ctx: GitBotContext, link: str) -> None:
        ctx.fmt.set_prefix('snippets')
        text, err = await handle_url(ctx, link)
        if text:
            await ctx.send(text)
        else:
            await ctx.send(err, style=MessageFormattingStyle.ERROR)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Snippets(bot))
