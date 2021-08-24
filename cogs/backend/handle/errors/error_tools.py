import discord
import traceback
from typing import Union
from discord.ext import commands
from lib.globs import Mgr


def is_error_case(ctx: commands.Context, cls, error) -> bool:
    if isinstance(error, cls) and not silenced(ctx, cls):
        return True
    return False


def silenced(ctx: commands.Context, error) -> bool:
    return bool(getattr(ctx, f'__silence_{Mgr.pascal_to_snake_case(error.__class__.__name__)}_error__', False))


async def respond_to_command_doesnt_exist(ctx: commands.Context, error: commands.CommandNotFound) -> None:
    await Mgr.enrich_context(ctx)
    ctx.fmt.set_prefix('errors command_not_found')
    embed: discord.Embed = discord.Embed(
        color=0x0384fc,
        title=ctx.l.errors.command_not_found.title,
        description=ctx.fmt('description',
                            f'```haskell\n{str(ctx.bot.command_prefix).strip()} '
                            f'{(closest_existing_command_from_error(ctx.bot, error))}```')
    )
    embed.set_footer(text=ctx.l.errors.command_not_found.footer)
    await ctx.send(embed=embed)


async def log_error_in_discord(ctx: commands.Context, error: Exception) -> None:
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
            embed: discord.Embed = discord.Embed(
                color=0x0384fc,
                title=f'Nonexistent command!',
                description=f'```{(error := str(error))}```'
            )
            embed.set_footer(text=f'Closest existing command: "' + closest_existing_command_from_error(ctx.bot, error))
        else:
            return
        embed.add_field(name='Location',
                        value=f'**Guild ID:** `{guild_id}`\n**Author ID:** `{ctx.author.id}`',
                        inline=False)
        await channel.send(embed=embed)


def closest_existing_command_from_error(bot: commands.Bot, error: Union[commands.CommandNotFound, str]) -> str:
    return str(Mgr.get_closest_match_from_iterable(
        (error := str(error))[error.index('"') + 1:error.rindex('"')],
        map(str, bot.walk_commands())))


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
