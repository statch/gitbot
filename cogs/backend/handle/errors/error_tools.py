import discord
import traceback
from typing import Optional
from discord.ext import commands
from lib.globs import Mgr
from lib.structs import GitBotEmbed
from lib.structs.discord.context import GitBotContext


def silenced(ctx: GitBotContext, error) -> bool:
    return bool(getattr(ctx, f'__silence_{Mgr.pascal_to_snake_case(error.__class__.__name__)}_error__', False))


async def respond_to_command_doesnt_exist(ctx: GitBotContext, error: commands.CommandNotFound) -> discord.Message:
    ctx.fmt.set_prefix('errors command_not_found')
    embed: GitBotEmbed = GitBotEmbed(
        color=0x0384fc,
        title=ctx.l.errors.command_not_found.title,
        description=ctx.fmt('description',
                            f'```haskell\n{str(ctx.bot.command_prefix).strip()} '
                            f'{(closest_existing_command_from_error(ctx.bot, error))}```'),
        footer=ctx.l.errors.command_not_found.footer
    )
    return await ctx.send(embed=embed)


async def log_error_in_discord(ctx: GitBotContext, error: Exception) -> Optional[discord.Message]:
    channel: discord.TextChannel = await ctx.bot.fetch_channel(853247229036593164)
    if channel:
        guild_id: str = str(ctx.guild.id) if not isinstance(ctx.channel, discord.DMChannel) else 'DM'
        if ctx.command:
            embed: discord.Embed = discord.Embed(
                color=0xda4353,
                title=f'Error in `{ctx.command}` command'
            )
            embed.add_field(name='Message', value=f'```{error}```', inline=False)
            embed.add_field(name='Traceback', value=f'```{format_tb(error.__traceback__)}```', inline=False)
            embed.add_field(name='Arguments',
                            value=f'```properties\nargs={format_args(ctx.args)}\nkwargs={format_kwargs(ctx.kwargs)}```',
                            inline=False)
        elif isinstance(error, commands.CommandNotFound):
            embed: GitBotEmbed = GitBotEmbed(
                color=0x0384fc,
                title=f'Nonexistent command!',
                description=f'```{(error := str(error))}```',
                footer=f'Closest existing command: ' + closest_existing_command_from_error(ctx.bot, error)
            )
        else:
            return
        embed.add_field(name='Location',
                        value=f'**Guild ID:** `{guild_id}`\n**Author ID:** `{ctx.author.id}`',
                        inline=False)
        return await channel.send(embed=embed)


def closest_existing_command_from_error(bot: commands.Bot, error: commands.CommandNotFound | str) -> str:
    return str(Mgr.get_closest_match_from_iterable(
        (error := str(error))[error.index('"') + 1:error.rindex('"')],
        filter(lambda cmd: cmd not in Mgr.env.hidden_commands, map(str, bot.walk_commands()))))


def format_tb(tb) -> str:
    return '\n\n'.join([i.strip() for i in traceback.format_tb(tb, -5)])


def format_args(args: list) -> str:
    for i, arg in enumerate(args):
        if repr(arg).startswith('<cogs'):
            args[i]: str = repr(arg).split()[0].strip('<')
        elif 'Context' in repr(arg):
            args[i]: str = 'ctx'
    return f"[{', '.join(args)}]"


def format_kwargs(kwargs: dict) -> str:
    items: str = ', '.join([f"{k}=\'{v}\'" for k, v in kwargs.items()])
    return f'dict({items})' if items else 'No keyword arguments'
