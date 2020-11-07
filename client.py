import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from ext.decorators import is_me
from cfg import globals

load_dotenv()
S = globals.Git

intents = discord.Intents.default()
intents.members = True
client = commands.Bot(command_prefix="git ", case_insensitive=True, intents=intents)
dir_paths: list = ['./cogs', './handle', './ext', './core']
exceptions: list = ["explicit_checks.py", "decorators.py", "manager.py"]
client.remove_command("help")


# Before a command is ran
async def before_invoke(ctx):
    await ctx.channel.trigger_typing()


client.before_invoke(before_invoke)

for directory in dir_paths:
    for file in os.listdir(directory):
        if file.endswith('.py') and file not in exceptions:
            client.load_extension(f"{directory[2:]}.{file[:-3]}")


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
    print(f'The bot is ready.\ndiscord.py version: {discord.__version__}\n')


client.run(os.getenv('BOT_TOKEN'))
