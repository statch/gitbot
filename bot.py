import os
import discord
import logging
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

PRODUCTION: bool = bool(int(os.getenv('PRODUCTION')))
PREFIX: str = str(os.getenv('PREFIX'))

intents = discord.Intents.default()
intents.bans = False
intents.voice_states = False

bot = commands.Bot(command_prefix=f'{PREFIX} ', case_insensitive=True,
                   intents=intents, help_command=None,
                   guild_ready_timeout=1, max_messages=None,
                   description='Seamless GitHub-Discord integration.',
                   fetch_offline_members=False)

dir_paths: list = ['./cogs', './handle', './ext', './core']
exceptions: list = ["explicit_checks.py", "decorators.py", "manager.py", "api.py"]
staging_exceptions: list = ['topgg.py'] if not PRODUCTION else []
botlist_folders: list = []

logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s: %(message)s')
logging.getLogger('asyncio').setLevel(logging.WARNING)
logging.getLogger('discord.gateway').setLevel(logging.WARNING)
logger = logging.getLogger('main')

bot.logger = logger


# Before a command is ran
async def before_invoke(ctx: commands.Context):
    await ctx.channel.trigger_typing()


bot.before_invoke(before_invoke)

extensions = [
    'cogs.base.user',
    'cogs.base.org',
    'cogs.base.repo',
    'cogs.numbered.pr',
    'cogs.numbered.issue',
    'cogs.download',
    'cogs.lines',
    'cogs.info',
    'cogs.help',
    'cogs.config',
    'cogs.debug',
    'cogs.bot_info'
]

for extension in extensions:
    logger.info(f'Loading {extension}...')
    bot.load_extension(extension)

if PRODUCTION:  # Load botlist extensions if we are in a production environment
    for folder in os.listdir('./core/botlists'):
        if os.path.isdir(f'./core/botlists/{folder}'):
            logger.info(f'queueing {folder} to be loaded')
            botlist_folders.append((f'./core/botlists/{folder}', f"core.botlists.{folder}"))

    for folder in botlist_folders:
        for file in os.listdir(folder[0]):
            if file.endswith('.py'):
                logger.info(f'loading extension: {folder[1]}.{file[:-3]}')
                bot.load_extension(f"{folder[1]}.{file[:-3]}")


@bot.check
async def global_check(ctx: commands.Context) -> bool:
    if not isinstance(ctx.channel, discord.DMChannel) and ctx.guild.unavailable:
        return False

    return True


@bot.event
async def on_ready():
    logger.info(f'The bot is ready.')
    logger.info(f'discord.py version: {discord.__version__}\n')


if __name__ == '__main__':
    bot.run(os.getenv('BOT_TOKEN'))
