import os
import discord
import logging
from discord.ext import commands
from dotenv import load_dotenv
from ext.decorators import is_me

load_dotenv()

PRODUCTION: bool = bool(int(os.getenv('PRODUCTION')))

intents = discord.Intents.default()
intents.bans = False
intents.voice_states = False

bot = commands.Bot(command_prefix='%s ' % str(os.getenv('PREFIX')), case_insensitive=True,
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

for directory in dir_paths:
    for file in os.listdir(directory):
        if file.endswith('.py') and file not in exceptions + staging_exceptions:
            logger.info(f'loading extension: {directory[2:]}.{file[:-3]}')
            bot.load_extension(f"{directory[2:]}.{file[:-3]}")

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


@bot.command(name='load', aliases=["--load"])
@is_me()
async def _load_extension(ctx, extension, path='cogs'):
    if str(extension).startswith('_'):
        await ctx.send(f"<:github:772040411954937876>  This file isn't meant to be used as an extension!")
        return
    if str(extension).endswith('.py'):
        extension: str = extension[:-3]
    try:
        bot.load_extension(f"{path}.{extension}")
    except (commands.ExtensionAlreadyLoaded, commands.ExtensionNotFound) as e:
        if isinstance(e, commands.ExtensionAlreadyLoaded):
            await ctx.send(f"<:github:772040411954937876>  This extension is **already loaded!**")
        elif isinstance(e, commands.ExtensionNotFound):
            await ctx.send(f"<:github:772040411954937876>  I couldn't find that extension!")
        return
    await ctx.send(f"<:github:772040411954937876>  **{extension}** extension has been **loaded.**")


@bot.command(name='unload', aliases=["--unload"])
@is_me()
async def _unload_extension(ctx, extension, path='cogs'):
    if str(extension).startswith('_'):
        await ctx.send(f"<:github:772040411954937876>  This file isn't meant to be used as an extension!")
        return
    if str(extension).endswith('.py'):
        extension: str = extension[:-3]
    try:
        bot.unload_extension(f"{path}.{extension}")
    except (commands.ExtensionNotLoaded, commands.ExtensionNotFound) as e:
        if isinstance(e, commands.ExtensionNotLoaded):
            await ctx.send(f"<:github:772040411954937876>  This extension **isn't loaded!**")
        elif isinstance(e, commands.ExtensionNotFound):
            await ctx.send(f"<:github:772040411954937876>  I couldn't find that extension!")
        return
    await ctx.send(f"<:github:772040411954937876>  **{extension}** extension has been **unloaded.**")


@bot.command(name='reload', aliases=["--reload"])
@is_me()
async def _reload_extension(ctx, extension, path='cogs'):
    if str(extension).startswith('_'):
        await ctx.send(f"<:github:772040411954937876>  This file isn't meant to be used as an extension!")
        return
    if str(extension).endswith('.py'):
        extension: str = extension[:-3]
    try:
        bot.reload_extension(f"{path}.{extension}")
    except (commands.ExtensionNotLoaded, commands.ExtensionNotFound) as e:
        if isinstance(e, commands.ExtensionNotLoaded):
            await ctx.send(f"<:github:772040411954937876>  This extension **isn't loaded!**")
        elif isinstance(e, commands.ExtensionNotFound):
            await ctx.send(f"<:github:772040411954937876>  I couldn't find that extension!")
        return
    await ctx.send(f"<:github:772040411954937876> **{extension}** extension has been **reloaded.**")


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
