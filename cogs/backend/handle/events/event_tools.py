import asyncio
import functools
import discord
from discord.ext import commands
from lib.globs import Mgr
from lib.utils import regex
from cogs.github.other.snippets.snippet_tools import handle_url, gen_carbon_inmemory
from typing import Optional


def set_handler_ctx_attributes(ctx: commands.Context) -> commands.Context:
    ctx.__silence_max_concurrency_error__ = True
    ctx.__silence_command_on_cooldown_error__ = True
    return ctx


@commands.command('snippet-no-error')
@commands.cooldown(3, 20, commands.BucketType.guild)
@commands.max_concurrency(6, wait=True)
async def silent_snippet_command(ctx: commands.Context) -> Optional[discord.Message]:
    codeblock: Optional[str] = None
    if ctx.message.content not in Mgr.carbon_attachment_cache:
        if ((await Mgr.get_autoconv_config(ctx))['link'] and (regex.GITHUB_LINES_RE.search(ctx.message.content)
                                                              or regex.GITLAB_LINES_RE.search(ctx.message.content))):
            codeblock: Optional[str] = (await handle_url(ctx,
                                                         ctx.message.content,
                                                         max_line_count=Mgr.env.carbon_len_threshold,
                                                         wrap_in_codeblock=False))[0]
        elif (result := Mgr.extract_content_from_codeblock(ctx.message.content)) and \
                (await Mgr.get_autoconv_config(ctx))['codeblock']:
            codeblock: str = result
        if codeblock and len(codeblock.splitlines()) < Mgr.env.carbon_len_threshold:
            reply: discord.Message = await ctx.reply(file=discord.File(filename='snippet.png',
                                                                       fp=await gen_carbon_inmemory(codeblock)),
                                                     mention_author=False)
            Mgr.carbon_attachment_cache[ctx.message.content] = reply.attachments[0].url
            return reply
    elif attachment_url := Mgr.carbon_attachment_cache.get(ctx.message.content):
        return await ctx.reply(attachment_url, mention_author=False)


async def handle_codeblock_message(ctx: commands.Context) -> Optional[discord.Message]:
    set_handler_ctx_attributes(ctx)
    return await ctx.invoke(silent_snippet_command)


@commands.command('resolve-url-no-error')
@commands.cooldown(3, 20, commands.BucketType.guild)
@commands.max_concurrency(10, wait=True)
async def resolve_url_command(ctx: commands.Context) -> Optional[discord.Message]:
    if cmd_data := await Mgr.get_link_reference(ctx):
        if isinstance(cmd_data.command, commands.Command):
            return await ctx.invoke(cmd_data.command, **cmd_data.kwargs)
        else:
            nonce: int = id(ctx)
            for command, kwargs in zip(cmd_data.command, cmd_data.kwargs):
                ctx.send = functools.partial(ctx.send, nonce=nonce)
                await ctx.invoke(command, **kwargs)
                try:
                    message = await ctx.bot.wait_for('message',
                                                     check=lambda msg: (msg.channel.id == ctx.channel.id
                                                                        and msg.author.id == ctx.bot.user.id),
                                                     timeout=1.5)
                    if message.nonce == nonce:
                        return message
                    continue
                except asyncio.TimeoutError:
                    continue


async def handle_link_message(ctx: commands.Context) -> Optional[discord.Message]:
    set_handler_ctx_attributes(ctx)

    async def _send(*args, **kwargs):
        if 'embed' in kwargs:
            await ctx.reply(*args, **kwargs, mention_author=False)

    ctx.send = _send
    return await ctx.invoke(resolve_url_command)


async def build_guild_embed(bot: commands.Bot, guild: discord.Guild, state: bool = True) -> discord.Embed:
    if state:
        title: str = f'{Mgr.e.checkmark}  Joined a new guild!'
        color: int = 0x33ba7c
    else:
        title: str = f'{Mgr.e.failure}  Removed from a guild.'
        color: int = 0xda4353

    embed: discord.Embed = discord.Embed(
        title=title,
        color=color,
    )
    owner = await bot.fetch_user(guild.owner_id)
    embed.add_field(name='Name', value=str(guild))
    embed.add_field(name='Members', value=str(guild.member_count))
    embed.add_field(name='ID', value=f"`{str(guild.id)}`")
    embed.add_field(name='Owner', value=str(owner))
    embed.add_field(name='Created at', value=str(guild.created_at.strftime('%e, %b %Y')))
    embed.add_field(name='Channels', value=str(len(guild.channels) - len(guild.categories)))
    embed.set_footer(text=f"Now in {len(bot.guilds)} guilds")
    embed.set_thumbnail(url=guild.icon_url)

    return embed
