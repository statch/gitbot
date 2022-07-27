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
from lib.globs import Mgr
from typing import Optional, Iterable
from lib.typehints import EmbedLike
from lib.structs import DictProxy
from lib.structs.discord.embed import GitBotEmbed
from lib.structs.discord.commands import GitBotCommand, GitBotCommandGroup

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
    def __init__(self, **attrs):
        self.command: GitBotCommand | GitBotCommandGroup
        self.__nocache__ = False
        self.__autoinvoked__ = False
        self.fmt = Mgr.fmt(self)
        self.l = None  # noqa
        self.data: Optional[dict] = None  # field used by chained invocations and quick access
        self.invoked_with_stored: bool = False
        super().__init__(**attrs)

    @staticmethod
    def _format_content(content: str, style: MessageFormattingStyle | str) -> str:
        match MessageFormattingStyle(style):
            case MessageFormattingStyle.ERROR:
                return f'{Mgr.e.err}  {content}'
            case MessageFormattingStyle.SUCCESS:
                return f'{Mgr.e.checkmark}  {content}'
            case MessageFormattingStyle.INFO:
                return f'{Mgr.e.github}  {content}'
            case _:
                return content

    @property
    def lp(self) -> DictProxy:
        """
        Returns a prefixed subset of the context locale.
        """
        return Mgr.get_nested_key(self.l, self.fmt.prefix.strip())

    async def send(self,
                   content: Optional[str] = None,
                   *,
                   tts: bool = False,
                   embed: Optional[EmbedLike] = None,
                   file: Optional[discord.File] = None,
                   files: Optional[Iterable[discord.File]] = None,
                   delete_after: Optional[int] = None,
                   nonce: Optional[int] = None,
                   allowed_mentions: Optional[discord.AllowedMentions] = None,
                   reference: Optional[discord.MessageReference] = None,
                   mention_author: bool = None,
                   style: MessageFormattingStyle | str = MessageFormattingStyle.DEFAULT) -> discord.Message:
        return await super().send(content=self._format_content(content, style), tts=tts,
                                  embed=embed, file=file,
                                  files=files, delete_after=delete_after,
                                  nonce=nonce, allowed_mentions=allowed_mentions,
                                  reference=reference, mention_author=mention_author)

    async def info(self, *args, **kwargs) -> discord.Message:
        return await self.send(*args, style=MessageFormattingStyle.INFO, **kwargs)

    async def success(self, *args, **kwargs) -> discord.Message:
        return await self.send(*args, style=MessageFormattingStyle.SUCCESS, **kwargs)

    async def error(self, *args, **kwargs) -> discord.Message:
        return await self.send(*args, style=MessageFormattingStyle.ERROR, **kwargs)

    async def success_embed(self, text: str, **kwargs) -> discord.Message:
        return await GitBotEmbed.success(text, **kwargs).send(self)

    async def prepare(self) -> None:
        self.l = await Mgr.get_locale(self)  # noqa

    async def group_help(self, subcommand_check: bool = True):
        """
        Used for root group methods without any additional logic.
        """
        parent: Optional[GitBotCommand | GitBotCommandGroup] = (self.command.parent if not
                                                                isinstance(self.command,
                                                                           GitBotCommandGroup) else self.command)
        if parent and (not self.invoked_subcommand or not subcommand_check):
            return await parent.send_help(self)
