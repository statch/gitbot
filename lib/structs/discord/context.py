# coding: utf-8

"""
Custom Discord context interface implementation for GitBot
~~~~~~~~~~~~~~~~~~~
A non-native replacement for the context object provided in discord.ext.commands
:copyright: (c) 2020-present statch
:license: CC BY-NC-ND 4.0, see LICENSE for more details.
"""
import discord
import enum
from discord.ext import commands
from typing import Optional, Any, Sequence
from lib.typehints import EmbedLike
from lib.structs import DictProxy
from lib.structs.discord.embed import GitBotEmbed
from lib.structs.discord.commands import GitBotCommand, GitBotCommandGroup, GitBotHybridCommandGroup
from typing import TYPE_CHECKING, Union
from collections.abc import Awaitable, Callable

if TYPE_CHECKING:
    from aiohttp import ClientSession
    from lib.structs import CheckFailureCode, GitBot
    from lib.api.github import GitHubQueryDebugInfo

__all__: tuple = ('MessageFormattingStyle', 'GitBotContext')


class MessageFormattingStyle(enum.Enum):
    """
    Enumeration of message formatting styles.
    """

    DEFAULT: str = 'default'
    ERROR: str = 'error'
    SUCCESS: str = 'success'
    INFO: str = 'info'


class GitBotContext(commands.Context):
    bot: 'GitBot'
    command: GitBotCommand | GitBotCommandGroup
    check_failure_code: Union[int, 'CheckFailureCode'] | None = None
    gh_query_debug: Optional['GitHubQueryDebugInfo'] = None
    lines_total: int | None = None
    __nocache__: bool = False
    __autoinvoked__: bool = False
    __silence_error_calls__: bool = False

    def __init__(self, **attrs):
        self.command: GitBotCommand | GitBotCommandGroup
        super().__init__(**attrs)
        self.session: ClientSession = self.bot.session
        self.fmt = self.bot.mgr.fmt(self)
        self.l = None  # noqa
        self.data: Optional[dict] = None  # field used by chained invocations and quick access
        self.invoked_with_stored: bool = False

    def _format_content(self, content: str, style: MessageFormattingStyle | str) -> str:
        match MessageFormattingStyle(style):
            case MessageFormattingStyle.ERROR:
                return f'{self.bot.mgr.e.error}  {content}'
            case MessageFormattingStyle.SUCCESS:
                return f'{self.bot.mgr.e.checkmark}  {content}'
            case MessageFormattingStyle.INFO:
                return f'{self.bot.mgr.e.github}  {content}'
            case _:
                return content

    @property
    def lp(self) -> DictProxy:
        """
        Returns a prefixed subset of the context locale.
        """
        return self.bot.mgr.get_nested_key(self.l, self.fmt.prefix.strip())

    async def send(self,
                   content: str | None = None,
                   *,
                   tts: bool = False,
                   embed: EmbedLike | None = None,
                   embeds: Sequence[EmbedLike] | None = None,
                   file: discord.File | None = None,
                   files: Sequence[discord.File] | None = None,
                   stickers: Sequence[discord.GuildSticker | discord.StickerItem] | None = None,
                   delete_after: float | None = None,
                   nonce: str | int | None = None,
                   allowed_mentions: discord.AllowedMentions | None = None,
                   reference: discord.Message | discord.MessageReference | discord.PartialMessage | None = None,
                   mention_author: bool | None = None,
                   view: discord.ui.View | None = None,
                   suppress_embeds: bool = False,
                   ephemeral: bool = False,
                   style: MessageFormattingStyle | str = MessageFormattingStyle.DEFAULT,
                   view_on_url: None | str = None) -> discord.Message:
        if view_on_url is not None:
            if view is None:
                view = discord.ui.View()
            domain: str = view_on_url.split('/')[2]
            button: discord.ui.Button = discord.ui.Button(style=discord.ButtonStyle.link, url=view_on_url)
            match domain:
                case 'github.com':
                    button.label = self.l.generic.view.on_github
                    button.emoji = self.bot.mgr.e.github
                case _:
                    button.label = self.l.generic.view.more.format(domain)
                    button.emoji = self.bot.mgr.e.info
            view.add_item(button)
        return await super().send(content=self._format_content(content, style), tts=tts,
                                  embed=embed, embeds=embeds,
                                  file=file, files=files,
                                  stickers=stickers, delete_after=delete_after,
                                  nonce=nonce, allowed_mentions=allowed_mentions,
                                  reference=reference, mention_author=mention_author,
                                  view=view, suppress_embeds=suppress_embeds, ephemeral=ephemeral)

    async def invoke(self,
                     command: GitBotCommand | Callable[['GitBotContext'], Awaitable[Any, ...]],
                     /,
                     *args,
                     **kwargs) -> Any:
        await super().invoke(command, *args, **kwargs)

    async def info(self, *args, **kwargs) -> discord.Message:
        return await self.send(*args, style=MessageFormattingStyle.INFO, **kwargs)

    async def success(self, *args, **kwargs) -> discord.Message:
        return await self.send(*args, style=MessageFormattingStyle.SUCCESS, **kwargs)

    async def error(self, *args, **kwargs) -> discord.Message:
        if not self.__silence_error_calls__:
            return await self.send(*args, style=MessageFormattingStyle.ERROR, **kwargs)

    async def success_embed(self, text: str, **kwargs) -> discord.Message:
        return await GitBotEmbed.success(text, **kwargs).send(self)

    async def prepare(self) -> None:
        self.l = await self.bot.db.users.get_locale(self)  # noqa

    async def group_help(self, subcommand_check: bool = True):
        """
        Used for root group methods without any additional logic.
        """
        parent: Optional[GitBotCommand | GitBotCommandGroup] = (self.command.parent if not
        isinstance(self.command, (GitBotCommandGroup, GitBotHybridCommandGroup)) else self.command)
        if parent and (not self.invoked_subcommand or not subcommand_check):
            return await parent.send_help(self)
