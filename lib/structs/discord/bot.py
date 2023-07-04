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
import aiohttp
import platform
import aiofiles
import itertools
import sentry_sdk
from dotenv import load_dotenv
from lib.api.github.github import GitHubAPI
from lib.api.carbonara import Carbon
from lib.api.pypi import PyPIAPI
from lib.api.crates import CratesIOAPI
from lib.manager import Manager
from time import perf_counter
from discord.ext import commands
from lib.structs.discord.context import GitBotContext
from lib.structs.discord.commands import GitBotCommand, GitBotCommandGroup
from lib.utils.logging_utils import GitBotLoggingStreamHandler

load_dotenv()

__all__: tuple = ('GitBot',)


class GitBot(commands.AutoShardedBot):
    session: aiohttp.ClientSession | None = None
    github: GitHubAPI | None
    carbon: Carbon | None = None
    pypi: PyPIAPI | None = None
    crates: CratesIOAPI | None = None
    mgr: Manager | None = None
    runtime_vars: dict[str, str] = {}
    statch_guild: discord.Guild | None = None
    error_log_channel: discord.TextChannel | None = None

    def __init__(self, **kwargs):
        self.__init_start: float = perf_counter()
        self.user_id_blacklist: set = set()
        super().__init__(command_prefix=f'{os.getenv("PREFIX")} ', case_insensitive=True,
                         intents=discord.Intents(messages=True, message_content=True, guilds=True,
                                                 guild_reactions=True),
                         help_command=None, guild_ready_timeout=1,
                         status=discord.Status.online, description='Seamless GitHub-Discord integration.',
                         fetch_offline_members=False, **kwargs)

    def _setup_uvloop(self):
        if os.name != 'nt':
            self.logger.info('Installing uvloop...')
            __import__('uvloop').install()
        else:
            self.logger.info('Skipping uvloop install.')

    async def _setup_cloc(self) -> None:
        if not os.path.exists('cloc.pl'):
            self.logger.info('CLOC script not found, downloading...')
            res: aiohttp.ClientResponse = await self.session.get(
                'https://github.com/AlDanial/cloc/releases/download/v1.90/cloc-1.90.pl')
            async with aiofiles.open('cloc.pl', 'wb') as fp:
                await fp.write(await res.content.read())
            self.logger.info('CLOC script downloaded.')
        else:
            self.logger.info('CLOC script found, skipping download.')

    def _setup_sentry(self) -> None:
        if self.mgr.env.production and (dsn := self.mgr.env.get('sentry_dsn')):
            self.logger.info('Setting up Sentry...')
            sentry_sdk.init(
                dsn=dsn,
                traces_sample_rate=0.5
            )
        else:
            self.logger.info('Sentry not enabled/configured - skipping')

    def _setup_logging(self):
        logging.basicConfig(level=logging.INFO, handlers=[GitBotLoggingStreamHandler()], force=True)
        logging.getLogger('asyncio').setLevel(logging.WARNING)
        logging.getLogger('discord.gateway').setLevel(logging.WARNING)
        logging.getLogger('discord.client').setLevel(logging.INFO)
        self.logger: logging.Logger = logging.getLogger('bot')

    @property
    def github(self) -> GitHubAPI | None:
        return next(self.__internal_github_instances_cycle) if self._internal_github_instances else None

    async def _setup_github(self) -> None:
        self._internal_github_instances: tuple[GitHubAPI, ...] = (
            GitHubAPI(self, os.getenv('GITHUB_MAIN'), self.session),
            GitHubAPI(self, os.getenv('GITHUB_SECONDARY'), self.session)
        )
        self.__internal_github_instances_cycle: itertools.cycle = itertools.cycle(self._internal_github_instances)

    async def _setup_services(self) -> None:
        self.session: aiohttp.ClientSession = aiohttp.ClientSession(loop=self.loop)
        await self._setup_github()
        self.mgr: Manager = Manager(self, self.github)
        self.carbon: Carbon = Carbon(self.session)
        self.pypi: PyPIAPI = PyPIAPI(self.session)
        self.crates: CratesIOAPI = CratesIOAPI(self.session)

    async def get_context(self, message: discord.Message, *, cls=GitBotContext) -> GitBotContext:
        ctx: GitBotContext = await super().get_context(message, cls=cls)
        await ctx.prepare()
        return ctx

    def command(self, *args, **kwargs):
        return super().command(*args, **kwargs, cls=GitBotCommand)

    def group(self, *args, **kwargs):
        return super().group(*args, **kwargs, cls=GitBotCommandGroup)

    def _set_runtime_vars(self) -> None:
        self.runtime_vars: dict[str, str] = {
            'discord.py-version': discord.__version__,
            'gitbot-commit': self.mgr.get_current_commit(short=False),
        }

    async def setup_statch_specific(self) -> None:
        self.statch_guild: discord.Guild | None = await self.fetch_guild(737430006271311913, with_counts=False)
        async for ban in self.statch_guild.bans():
            self.user_id_blacklist.add(ban.user.id)
        self.logger.info('Fetched %i blacklisted users.', len(self.user_id_blacklist))

    async def setup_hook(self) -> None:
        if not os.path.exists('./tmp'):
            os.mkdir('tmp')
        self._setup_logging()
        await self._setup_services()
        self.logger.setLevel(getattr(logging, self.mgr.env.log_level.upper(), self.mgr.env.log_level))
        self._set_runtime_vars()
        self._setup_sentry()
        self._setup_uvloop()
        await self._setup_cloc()
        await self.load_cogs()
        self.error_log_channel: discord.TextChannel = await self.fetch_channel(self.mgr.env.error_log_channel_id)
        test_guild_id: int | None = self.mgr.env.get('test_guild_id')
        if test_guild := discord.Object(id=test_guild_id) if test_guild_id else None:
            self.tree.copy_global_to(guild=test_guild)
        if self.mgr.env.sync_commands_on_startup:
            await self.tree.sync(guild=test_guild)
        await self.setup_statch_specific()

    async def close(self) -> None:
        await super().close()
        await self.session.close()
        await self.github.session.close()

    async def on_ready(self) -> None:
        self.logger.info(f'Bot bootstrap time: {perf_counter() - self.__init_start:.3f}s')
        self.logger.info('The bot is ready!')
        self.logger.info(f'Running on {platform.system()} {platform.release()}')
        self.logger.info('Runtime vars:\n' + '\n'.join(f'- {k}: {v}' for k, v in self.runtime_vars.items()))

    async def load_cogs_from_dir(self, dir_: str) -> None:
        for obj in os.listdir(dir_):
            if os.path.isdir(f'{dir_}/{obj}'):
                await self.load_cogs_from_dir(f'{dir_}/{obj}')
            if obj.endswith('.py') and not obj.startswith('_'):
                await self.load_extension(f'{dir_.replace("/", ".")}.{obj[:-3]}')

    async def load_cogs(self) -> None:
        for subdir in os.listdir('cogs'):
            if os.path.isdir(f'cogs/{subdir}') and (subdir not in self.mgr.env.production_only_cog_subdirs
            if not self.mgr.env.production else True):
                await self.load_cogs_from_dir(f'cogs/{subdir}')

    async def load_extension(self, name: str, *, package=None):
        await super().load_extension(name, package=package)
        self.logger.info('Loaded extension: "%s"', name)

    async def unload_extension(self, name: str, *, package=None):
        await super().unload_extension(name, package=package)
        self.logger.info('Unloaded extension: "%s"', name)

    async def reload_extension(self, name: str, *, package=None):
        await super().reload_extension(name, package=package)
        self.logger.info('Reloaded extension: "%s"', name)
