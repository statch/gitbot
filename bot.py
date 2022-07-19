import discord
from lib.globs import Mgr
from discord.ext import commands
from lib.utils.decorators import restricted, gitbot_command
from lib.structs.discord.bot import GitBot
from lib.structs.discord.context import GitBotContext

intents: discord.Intents = discord.Intents(
    messages=True,
    guilds=True,
    guild_reactions=True
)

bot: GitBot = GitBot(command_prefix=f'{Mgr.env.prefix} ', case_insensitive=True,
                     intents=intents, help_command=None,
                     guild_ready_timeout=1, status=discord.Status.online,
                     description='Seamless GitHub-Discord integration.',
                     fetch_offline_members=False)


async def do_cog_op(ctx: GitBotContext, cog: str, op: str) -> None:
    if (cog := cog.lower()) == 'all':
        done: int = 0
        try:
            for ext in bot.extensions:
                getattr(bot, f'{op}_extension')(str(ext))
                done += 1
        except commands.ExtensionError as e:
            await ctx.error(f'**Exception during batch-{op}ing:**\n```{e}```')
        else:
            await ctx.success(f'All extensions **successfully {op}ed.** ({done})')
    else:
        try:
            getattr(bot, f'{op}_extension')(cog)
        except commands.ExtensionError as e:
            await ctx.error(f'**Exception while {op}ing** `{cog}`**:**\n```{e}```')
        else:
            await ctx.success(f'**Successfully {op}ed** `{cog}`.')


@gitbot_command(name='reload', hidden=True)
@restricted()
async def reload_command(ctx: GitBotContext, cog: str) -> None:
    await do_cog_op(ctx, cog, 'reload')


@gitbot_command(name='load', hidden=True)
@restricted()
async def load_command(ctx: GitBotContext, cog: str) -> None:
    await do_cog_op(ctx, cog, 'load')


@gitbot_command(name='unload', hidden=True)
@restricted()
async def unload_command(ctx: GitBotContext, cog: str) -> None:
    await do_cog_op(ctx, cog, 'unload')


@bot.check
async def global_check(ctx: GitBotContext) -> bool:
    if not isinstance(ctx.channel, discord.DMChannel) and ctx.guild.unavailable:
        return False

    return True


@bot.before_invoke
async def before_invoke(ctx: GitBotContext) -> None:
    if str(ctx.command) not in Mgr.env.no_typing_commands:
        await ctx.channel.trigger_typing()
