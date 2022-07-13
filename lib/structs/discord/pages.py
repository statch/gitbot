"""
Custom Discord embed paging interface implementation for GitBot
~~~~~~~~~~~~~~~~~~~
A set of objects used to handle embed pagination inside Discord
:copyright: (c) 2020-present statch
:license: CC BY-NC-ND 4.0, see LICENSE for more details.
"""

import discord
import asyncio
from time import time
from enum import Enum
from discord.ext import commands
from typing import Optional, NoReturn, TYPE_CHECKING
if TYPE_CHECKING:
    from lib.structs.discord.context import GitBotContext
    from lib.structs.discord.bot import GitBot
from lib.structs.discord.embed import GitBotEmbed, GitBotCommandState
from lib.globs import Mgr


__all__: tuple = ('EmbedPagesControl', 'ACTIONS', 'EmbedPages')


class EmbedPagesControl(Enum):
    FIRST = '⏮'
    BACK = '◀'
    STOP = '⏹'
    NEXT = '▶'
    LAST = '⏭'


ACTIONS: set = {e.value for e in EmbedPagesControl}


class EmbedPagesPermissionError(Exception):
    """Raised if the bot doesn't have required permissions to run the paginator"""


class EmbedPages:
    """
    A simple class that handles embed pagination.

    :param pages: A list of embeds to paginate.
    :param timeout: The timeout in seconds (Websocket events + internal)
    :param lifespan: The total lifespan of the command -
                     no matter if an action occurred or not it will close after this time.
    """

    def __init__(self,
                 pages: Optional[list[GitBotEmbed | discord.Embed]] = None,
                 timeout: int = 75,
                 lifespan: int = 300,
                 action_polling_rate: float = 0.5):
        self.pages: list = pages if pages else []
        self.lifespan: float = lifespan
        self.timeout: int = timeout
        self.current_page: int = 0
        self.action_polling_rate: float = action_polling_rate
        self.start_time: Optional[float] = None
        self.last_action_time: Optional[float] = None
        self.message: Optional[discord.Message] = None
        self.context: Optional['GitBotContext'] = None
        self.bot: Optional['GitBot'] = None

    @staticmethod
    def _ensure_perms(channel: discord.TextChannel) -> NoReturn:
        if not isinstance(channel, discord.DMChannel):
            permissions: discord.Permissions = channel.permissions_for(channel.guild.me)
            if not (permissions.administrator or all([permissions.manage_messages, permissions.add_reactions])):
                raise EmbedPagesPermissionError

    @property
    def current_page_string(self) -> str:
        """
        The current page number returned as a string (en_default: Page {x}/len(pages))
        """

        return f'{self.context.l.glossary.page} {self.current_page + 1}/{len(self.pages)}'

    @property
    def lifetime(self) -> float:
        """
        The total lifetime of the paginator
        """

        return time() - self.start_time

    @property
    def time_since_last_action(self) -> float:
        """
        The time since the last action was performed
        """

        return time() - self.last_action_time

    @property
    def should_die(self) -> bool:
        """
        Checks if the paginator should end its lifespan and edit its current embed accordingly
        """

        return self.time_since_last_action > self.timeout and self.lifetime < self.lifespan

    def add_page(self, page: GitBotEmbed | discord.Embed) -> None:
        """
        Add a new page to the paginator.
        """

        self.pages.append(page)

    def remove_page(self, page: GitBotEmbed | discord.Embed) -> None:
        """
        Remove a page from the paginator.
        """

        self.pages.remove(page)

    async def start(self, ctx: 'GitBotContext') -> None:
        """
        Start the paginator in the passed context.

        :param ctx: The context to start the paginator in.
        """

        self._ensure_perms(ctx.channel)
        self.start_time = time()
        self.context: GitBotContext = ctx
        self._edit_embed_footer(self.pages[self.current_page])
        message: discord.Message = await ctx.send(embed=self.pages[self.current_page])
        for embed in self.pages[1:]:
            self._edit_embed_footer(embed)
        self._set_initial_message_attrs(message)
        await self._add_controls()
        await self.__loop()

    async def edit(self, state: GitBotCommandState | int) -> None:
        """
        Edit the currently displayed embed with the given state

        :param state: The state to edit the embed with
        """

        embed: discord.Embed | GitBotEmbed = self.message.embeds[0]
        if state is GitBotCommandState.CLOSED:
            embed.set_footer(text=f'{self.context.l.generic.closed} | {self.current_page_string}')
            embed.colour = Mgr.c.discord.red
        elif state is GitBotCommandState.TIMEOUT:
            embed.set_footer(text=f'{self.context.l.generic.inactive} | {self.current_page_string}')
            embed.colour = Mgr.c.discord.yellow
        await self.message.edit(embed=embed)

    async def next_page(self):
        if self.current_page + 1 < len(self.pages):
            await self.update_page(self.current_page + 1)

    async def previous_page(self):
        if self.current_page > 0:
            await self.update_page(self.current_page - 1)

    async def to_first_page(self):
        await self.update_page(0)

    async def to_last_page(self):
        await self.update_page(len(self.pages) - 1)

    async def update_page(self, page: int):
        if 0 <= page < len(self.pages):
            self.current_page = page
            self.last_action_time: float = time()
            await self.message.edit(embed=self.pages[self.current_page])

    def _edit_embed_footer(self, embed: discord.Embed | GitBotEmbed) -> None:
        if embed in self.pages:
            page_str: str = f'{self.context.l.glossary.page} {self.pages.index(embed) + 1}/{len(self.pages)}'
        else:
            page_str: str = self.current_page_string

        if embed.footer.text == discord.Embed.Empty:
            return embed.set_footer(text=page_str)
        embed.set_footer(text=f'{embed.footer.text} | {page_str}')

    def _set_initial_message_attrs(self, message: discord.Message):
        self.start_time: float = time()
        self.last_action_time: float = self.start_time
        self.bot: commands.Bot = self.context.bot
        self.message: discord.Message = message

    async def _add_controls(self):
        if self.message:
            for control in EmbedPagesControl:
                await self.message.add_reaction(control.value)

    async def __loop(self):
        while True:
            if not self.should_die:
                reaction: discord.Reaction
                user: discord.Member | discord.User
                try:
                    Mgr.debug('Running reaction_add event waiter')
                    reaction, user = await self.bot.wait_for('reaction_add',
                                                             check=lambda r, u: (r.emoji in ACTIONS and
                                                                                 u == self.context.author and
                                                                                 (r.message.channel.id ==
                                                                                  self.context.channel.id)),
                                                             timeout=self.timeout)
                except asyncio.TimeoutError:
                    Mgr.debug(f'Event timeout with lifetime={self.lifetime} '
                              f'and time since last action={self.time_since_last_action}')
                    try:
                        await self.edit(GitBotCommandState.TIMEOUT)
                    except discord.errors.NotFound:
                        pass
                    finally:
                        break
                if self.time_since_last_action < self.action_polling_rate:
                    await asyncio.sleep(self.action_polling_rate - self.time_since_last_action)
                action: EmbedPagesControl = EmbedPagesControl(reaction.emoji)
                match action:
                    case EmbedPagesControl.BACK:
                        await self.previous_page()
                    case EmbedPagesControl.NEXT:
                        await self.next_page()
                    case EmbedPagesControl.FIRST:
                        await self.to_first_page()
                    case EmbedPagesControl.LAST:
                        await self.to_last_page()
                    case EmbedPagesControl.STOP:
                        await self.edit(GitBotCommandState.CLOSED)
                        Mgr.debug('Stopping embed paginator loop - closed')
                        break
                Mgr.debug('Removing control reaction')
                await reaction.message.remove_reaction(reaction.emoji, user)
                Mgr.debug(f'Iteration complete with action {action.name}')
            else:
                Mgr.debug(f'Timeout with lifetime={self.lifetime} '
                          f'and time since last action={self.time_since_last_action}')
                await self.edit(GitBotCommandState.TIMEOUT)
                break

    def __add__(self, embed: discord.Embed | GitBotEmbed):
        self.add_page(embed)

    def __sub__(self, embed: discord.Embed | GitBotEmbed):
        self.remove_page(embed)

    def __len__(self):
        return len(self.pages)
