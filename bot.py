import os.path
import discord
import logging
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

logging.basicConfig(level=logging.INFO, format='[%(levelname)s:%(name)s]: %(message)s')
logging.getLogger('asyncio').setLevel(logging.WARNING)
logging.getLogger('discord.gateway').setLevel(logging.WARNING)
logger: logging.Logger = logging.getLogger('main')

extensions: list = [
    'cogs.backend.tasks.misc',
    'cogs.backend.debug.debug',
    'cogs.github.base.user',
    'cogs.github.base.org',
    'cogs.github.base.repo.repo',
    'cogs.github.numbered.pr',
    'cogs.github.numbered.issue',
    'cogs.github.complex.gist',
    'cogs.github.other.logs',
    'cogs.github.numbered.commits',
    'cogs.github.other.snippets.snippets',
    'cogs.github.other.license',
    'cogs.github.other.loc',
    'cogs.github.complex.workers.release_feed',
    'cogs.ecosystem.dev',
    'cogs.ecosystem.help',
    'cogs.ecosystem.config',
    'cogs.ecosystem.bot_info',
    'cogs.backend.handle.errors.errors',
    'cogs.backend.handle.events.events',
    'cogs.python.pypi',
    'cogs.rust.crates',
]

if Mgr.env.production:
    extensions.extend([f'cogs.botlists.major.{file[:-3]}' for file in os.listdir('cogs/botlists/major')])
    extensions.extend([f'cogs.botlists.minor.{file[:-3]}' for file in os.listdir('cogs/botlists/minor')])

for extension in extensions:
    logger.info('Loading %s...' % extension)
    bot.load_extension(extension)


async def do_cog_op(ctx: GitBotContext, cog: str, op: str) -> None:
    if (cog := cog.lower()) == 'all':
        done: int = 0
        try:
            for ext in extensions:
                getattr(bot, f'{op}_extension')(ext)
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


@bot.event
async def on_ready() -> None:
    logger.info('The bot is ready.')
    logger.info('discord.py version: %s\n' % discord.__version__)
