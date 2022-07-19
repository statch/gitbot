"""
Custom Discord bot interface implementation for GitBot
~~~~~~~~~~~~~~~~~~~
A non-native replacement for the bot object provided in discord.ext.commands
:copyright: (c) 2020-present statch
:license: CC BY-NC-ND 4.0, see LICENSE for more details.
"""

import os
import discord
import logging
from time import perf_counter
from discord.ext import commands
from lib.structs.discord.context import GitBotContext
from lib.structs.discord.commands import GitBotCommand, GitBotCommandGroup
from lib.globs import Mgr

__all__: tuple = ('GitBot',)


class GitBot(commands.Bot):
    runtime_vars: dict[str, str] = {
        'discord.py-version': discord.__version__,
        'gitbot-commit': Mgr.get_current_commit(short=False),
    }

    def __init__(self, *args, **kwargs):
        self.__init_start: float = perf_counter()
        super().__init__(*args, **kwargs)
        self._setup_logging()
        self.load_cogs()

    def _setup_logging(self):
        logging.basicConfig(level=getattr(logging, Mgr.env.log_level.upper(), logging.INFO),
                            format='[%(levelname)s:%(name)s]: %(message)s')
        logging.getLogger('asyncio').setLevel(logging.WARNING)
        logging.getLogger('discord.gateway').setLevel(logging.WARNING)
        self.logger: logging.Logger = logging.getLogger('main')

    async def get_context(self, message: discord.Message, *, cls=GitBotContext) -> GitBotContext:
        ctx: GitBotContext = await super().get_context(message, cls=cls)
        await ctx.prepare()
        return ctx

    def command(self, *args, **kwargs):
        return super().command(*args, **kwargs, cls=GitBotCommand)

    def group(self, *args, **kwargs):
        return super().group(*args, **kwargs, cls=GitBotCommandGroup)

    def load_extension(self, name: str, *, package=None):
        super().load_extension(name, package=package)
        self.logger.info(f'Loaded extension: "{name}"')

    def unload_extension(self, name: str, *, package=None):
        super().unload_extension(name, package=package)
        self.logger.info(f'Unloaded extension: "{name}"')

    def reload_extension(self, name: str, *, package=None):
        super().reload_extension(name, package=package)
        self.logger.info(f'Reloaded extension: "{name}"')

    def load_cogs_from_dir(self, dir_: str) -> None:
        for obj in os.listdir(dir_):
            if os.path.isdir(f'{dir_}/{obj}'):
                self.load_cogs_from_dir(f'{dir_}/{obj}')
            if obj.endswith('.py') and not obj.startswith('_'):
                self.load_extension(f'{dir_.replace("/", ".")}.{obj[:-3]}')

    def load_cogs(self) -> None:
        for subdir in os.listdir('cogs'):
            if os.path.isdir(f'cogs/{subdir}') and (subdir not in Mgr.env.production_only_cog_subdirs
                                                    if not Mgr.env.production else True):
                self.load_cogs_from_dir(f'cogs/{subdir}')

    async def on_ready(self) -> None:
        self.logger.info(f'Bot bootstrap time: {perf_counter() - self.__init_start:.3f}s')
        self.logger.info(f'The bot is ready!')
        self.logger.info(f'Runtime vars:\n' + '\n'.join(f'- {k}: {v}' for k, v in self.runtime_vars.items()))
