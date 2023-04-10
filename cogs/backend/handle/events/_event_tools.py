import time
import functools
import discord
from discord.ext import commands
from lib.utils import regex
from cogs.github.other.snippets._snippet_tools import handle_url, gen_carbon_inmemory
from typing import Optional
from lib.typehints import AutomaticConversionSettings
from lib.structs import GitBotEmbed, GitBot
from lib.structs.discord.context import GitBotContext


def set_handler_ctx_attributes(ctx: GitBotContext) -> commands.Context:
    ctx.__silence_max_concurrency_error__ = True
    ctx.__silence_command_on_cooldown_error__ = True
    return ctx


@commands.command('snippet-no-error', hidden=True)
@commands.cooldown(3, 20, commands.BucketType.guild)
@commands.max_concurrency(6, wait=True)
async def silent_snippet_command(ctx: GitBotContext) -> Optional[discord.Message]:
    codeblock: Optional[str] = None
    config: AutomaticConversionSettings = await ctx.bot.mgr.get_autoconv_config(ctx)  # noqa
    match_ = None  # put the match_ name in the namespace
    if (attachment_url := ctx.bot.mgr.carbon_attachment_cache.get(ctx.message.content)) and config['gh_lines'] == 2:
        ctx.bot.logger.debug('Responding with cached asset URL')
        return await ctx.reply(attachment_url, mention_author=False)
    elif (result := ctx.bot.mgr.extract_content_from_codeblock(ctx.message.content)) and config.get('codeblock', False):
        ctx.bot.logger.debug('Converting codeblock in MID %d into carbon snippet...', ctx.message.id)
        codeblock: str = result
    elif match_ := (regex.GITHUB_LINES_URL_RE.search(ctx.message.content)
                    or regex.GITLAB_LINES_URL_RE.search(ctx.message.content)):
        ctx.bot.logger.debug('Matched GitHub line URL: "%s" in MID %d', ctx.message.content, ctx.message.id)
        if config.get('gh_lines') == 2:
            ctx.bot.logger.debug('Converting URL in MID %d into carbon snippet...', ctx.message.id)
            codeblock: Optional[str] = (await handle_url(ctx,
                                                         ctx.message.content,
                                                         max_line_count=ctx.bot.mgr.env.carbon_len_threshold,
                                                         wrap_in_codeblock=False))[0]
        elif config.get('gh_lines') == 1:
            codeblock: Optional[str] = (await handle_url(ctx, ctx.message.content))[0]
            if codeblock:
                ctx.bot.logger.debug('Converting MID %d into codeblock...', ctx.message.id)
                return await ctx.reply(codeblock, mention_author=False)
    _1st_lineno: int = 1 if not match_ else match_.group('first_line_number')
    if codeblock and len(codeblock.splitlines()) < ctx.bot.mgr.env.carbon_len_threshold:
        start: float = time.time()
        reply: discord.Message = await ctx.reply(file=discord.File(filename='snippet.png',
                                                                   fp=await gen_carbon_inmemory(ctx,
                                                                                                codeblock, _1st_lineno)),
                                                 mention_author=False)
        ctx.bot.logger.debug('Carbon asset generation elapsed: %ds', time.time() - start)
        ctx.bot.mgr.carbon_attachment_cache[ctx.message.content] = reply.attachments[0].url
        return reply


async def handle_codeblock_message(ctx: GitBotContext) -> Optional[discord.Message]:
    set_handler_ctx_attributes(ctx)
    return await ctx.invoke(silent_snippet_command)


@commands.command('resolve-url-no-error', hidden=True)
@commands.cooldown(3, 20, commands.BucketType.guild)
@commands.max_concurrency(10, wait=True)
async def resolve_url_command(ctx: GitBotContext) -> Optional[discord.Message]:
    if (await ctx.bot.mgr.get_autoconv_config(ctx)).get('gh_url') and (cmd_data := await ctx.bot.mgr.get_link_reference(ctx)):
        ctx.bot.logger.debug('Invoking command(s) "%s" with kwargs: %s', str(cmd_data.command), str(cmd_data.kwargs))
        ctx.__autoinvoked__ = True
        if isinstance(cmd_data.command, commands.Command):
            return await ctx.invoke(cmd_data.command, **cmd_data.kwargs)
        else:
            nonce: int = id(ctx)
            for command, kwargs in zip(cmd_data.command, cmd_data.kwargs):
                ctx.bot.logger.debug('Running output checks with nonce: %d for command "%s"', nonce, str(command))
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
                except Exception: # noqa - we really don't care
                    continue


async def handle_link_message(ctx: GitBotContext) -> Optional[discord.Message]:
    set_handler_ctx_attributes(ctx)
    ctx.__silence_error_calls__ = True
    ctx.send = functools.partial(ctx.send, reference=ctx.message, mention_author=False)
    return await resolve_url_command(ctx)


async def build_guild_embed(bot: GitBot, guild: discord.Guild, state: bool = True) -> GitBotEmbed:
    if state:
        title: str = f'{bot.mgr.e.checkmark}  Joined a new guild!'
        color: int = 0x33ba7c
    else:
        title: str = f'{bot.mgr.e.failure}  Removed from a guild.'
        color: int = 0xda4353

    embed: GitBotEmbed = GitBotEmbed(
        title=title,
        color=color,
        footer=f"Now in {len(bot.guilds)} guilds",
        thumbnail=guild.icon.url
    )
    embed.add_field(name='Name', value=str(guild))
    try:
        embed.add_field(name='Members', value=str(guild.member_count))
    except AttributeError:
        embed.add_field(name='Members', value='`Unknown`')
    embed.add_field(name='ID', value=f"`{str(guild.id)}`")
    embed.add_field(name='Owner', value=str(await bot.fetch_user(guild.owner_id)))
    embed.add_field(name='Created at', value=str(guild.created_at.strftime('%e, %b %Y')))
    embed.add_field(name='Channels', value=str(len(guild.channels) - len(guild.categories)))
    return embed
