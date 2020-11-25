import os
import discord
import logging
from discord.ext import commands
from dotenv import load_dotenv
from ext.decorators import is_me

load_dotenv()

intents = discord.Intents.default()
intents.bans = False
intents.voice_states = False

client = commands.Bot(command_prefix="git ", case_insensitive=True,
                      intents=intents, help_command=None,
                      guild_ready_timeout=1, max_messages=None,
                      description='Seamless GitHub-Discord integration.',
                      fetch_offline_members=False)

dir_paths: list = ['./cogs', './handle', './ext', './core']
exceptions: list = ["explicit_checks.py", "decorators.py", "manager.py", "api.py"]
botlist_folders: list = []
    
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s: %(message)s')
logging.getLogger('asyncio').setLevel(logging.WARNING)
logging.getLogger('discord.gateway').setLevel(logging.WARNING)
logger = logging.getLogger('main')

client.logger = logger


# Before a command is ran
async def before_invoke(ctx):
    await ctx.channel.trigger_typing()


client.before_invoke(before_invoke)

for directory in dir_paths:
    for file in os.listdir(directory):
        if file.endswith('.py') and file not in exceptions:
            logger.info(f'loading extension: {directory[2:]}.{file[:-3]}')
            client.load_extension(f"{directory[2:]}.{file[:-3]}")

# Create a list of tuples consisting of a PATH and a string to load the extension
for folder in os.listdir('./core/botlists'):
    botlist_folders.append((f'./core/botlists/{folder}', f"core.botlists.{folder}"))

for folder in botlist_folders:
    for file in os.listdir(folder[0]):
        logger.info(f'loading extension: {folder[1]}.{file[:-3]}')
        client.load_extension(f"{folder[1]}.{file[:-3]}")


@client.command(name='load', aliases=["--load"])
@is_me()
async def _load_extension(ctx, extension, path='cogs'):
    if str(extension).startswith('_'):
        await ctx.send(f"<:github:772040411954937876>  This file isn't meant to be used as an extension!")
        return
    if str(extension).endswith('.py'):
        extension: str = extension[:-3]
    try:
        client.load_extension(f"{path}.{extension}")
    except (commands.ExtensionAlreadyLoaded, commands.ExtensionNotFound) as e:
        if isinstance(e, commands.ExtensionAlreadyLoaded):
            await ctx.send(f"<:github:772040411954937876>  This extension is **already loaded!**")
            return
        elif isinstance(e, commands.ExtensionNotFound):
            await ctx.send(f"<:github:772040411954937876>  I couldn't find that extension!")
            return
    await ctx.send(f"<:github:772040411954937876>  **{extension}** extension has been **loaded.**")


@client.command(name='unload', aliases=["--unload"])
@is_me()
async def _unload_extension(ctx, extension, path='cogs'):
    if str(extension).startswith('_'):
        await ctx.send(f"<:github:772040411954937876>  This file isn't meant to be used as an extension!")
        return
    if str(extension).endswith('.py'):
        extension: str = extension[:-3]
    try:
        client.unload_extension(f"{path}.{extension}")
    except (commands.ExtensionNotLoaded, commands.ExtensionNotFound) as e:
        if isinstance(e, commands.ExtensionNotLoaded):
            await ctx.send(f"<:github:772040411954937876>  This extension **isn't loaded!**")
            return
        elif isinstance(e, commands.ExtensionNotFound):
            await ctx.send(f"<:github:772040411954937876>  I couldn't find that extension!")
            return
    await ctx.send(f"<:github:772040411954937876>  **{extension}** extension has been **unloaded.**")


@client.command(name='reload', aliases=["--reload"])
@is_me()
async def _reload_extension(ctx, extension, path='cogs'):
    if str(extension).startswith('_'):
        await ctx.send(f"<:github:772040411954937876>  This file isn't meant to be used as an extension!")
        return
    if str(extension).endswith('.py'):
        extension: str = extension[:-3]
    try:
        client.reload_extension(f"{path}.{extension}")
    except (commands.ExtensionNotLoaded, commands.ExtensionNotFound) as e:
        if isinstance(e, commands.ExtensionNotLoaded):
            await ctx.send(f"<:github:772040411954937876>  This extension **isn't loaded!**")
            return
        elif isinstance(e, commands.ExtensionNotFound):
            await ctx.send(f"<:github:772040411954937876>  I couldn't find that extension!")
            return
    await ctx.send(f"<:github:772040411954937876> **{extension}** extension has been **reloaded.**")


@client.event
async def on_ready():
    logger.info(f'The bot is ready.')
    logger.info(f'discord.py version: {discord.__version__}\n')

if __name__ == '__main__':
    client.run(os.getenv('BOT_TOKEN'))
