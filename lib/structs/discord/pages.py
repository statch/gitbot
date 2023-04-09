"""
Custom Discord embed paging interface implementation for GitBot
~~~~~~~~~~~~~~~~~~~
A set of objects used to handle embed pagination inside Discord
:copyright: (c) 2020-present statch
:license: CC BY-NC-ND 4.0, see LICENSE for more details.
"""

import discord
from time import time
from typing import Optional, TYPE_CHECKING
if TYPE_CHECKING:
    from lib.structs.discord.context import GitBotContext
    from lib.structs.discord.bot import GitBot
from lib.structs.discord.embed import GitBotEmbed, GitBotCommandState
from lib.structs.discord.components import EmbedPagesControlView


__all__: tuple = ('EmbedPages',)


class EmbedPagesPermissionError(Exception):
    """Raised if the bot doesn't have required permissions to run the paginator"""


class EmbedPages:
    """
    A simple class that handles embed pagination.

    :param pages: A list of embeds to paginate.
    :param lifespan: The total lifespan of the command -
                     no matter if an action occurred or not it will close after this time.
    """

    def __init__(self,
                 pages: Optional[list[GitBotEmbed | discord.Embed]] = None,
                 lifespan: int = 900):
        self.pages: list = pages if pages else []
        self.lifespan: float = lifespan
        self.current_page: int = 0
        self.start_time: Optional[float] = None
        self.last_action_time: Optional[float] = None
        self.message: Optional[discord.Message] = None
        self.context: Optional['GitBotContext'] = None
        self.bot: Optional['GitBot'] = None

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
        return not self.lifetime < self.lifespan

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
        self.start_time = time()
        self.context: GitBotContext = ctx
        self._edit_embed_footer(self.pages[self.current_page])
        if not ctx.bot_permissions.manage_messages:
            raise EmbedPagesPermissionError('Bot does not have manage_messages permission')
        message: discord.Message = await ctx.send(embed=self.pages[self.current_page], view=EmbedPagesControlView(self))
        for embed in self.pages[1:]:
            self._edit_embed_footer(embed)
        self._set_initial_message_attrs(message)

    async def edit(self, state: GitBotCommandState | int) -> None:
        """
        Edit the currently displayed embed with the given state

        :param state: The state to edit the embed with
        """
        embed: discord.Embed | GitBotEmbed = self.message.embeds[0]
        if state is GitBotCommandState.CLOSED:
            embed.set_footer(text=f'{self.context.l.generic.closed} | {self.current_page_string}')
            embed.colour = self.bot.mgr.c.discord.red
        elif state is GitBotCommandState.TIMEOUT:
            embed.set_footer(text=f'{self.context.l.generic.inactive} | {self.current_page_string}')
            embed.colour = self.bot.mgr.c.discord.yellow
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
        page_str: str = (f'{self.context.l.glossary.page} {self.pages.index(embed) + 1}/{len(self.pages)}'
                         if embed in self.pages else self.current_page_string)
        if embed.footer.text is None:
            embed.set_footer(text=page_str)
        else:
            embed.set_footer(text=f'{embed.footer.text} | {page_str}')

    def _set_initial_message_attrs(self, message: discord.Message):
        self.start_time: float = time()
        self.last_action_time: float = self.start_time
        self.bot: 'GitBot' = self.context.bot
        self.message: discord.Message = message

    def __add__(self, embed: discord.Embed | GitBotEmbed):
        self.add_page(embed)

    def __sub__(self, embed: discord.Embed | GitBotEmbed):
        self.remove_page(embed)

    def __len__(self):
        return len(self.pages)
