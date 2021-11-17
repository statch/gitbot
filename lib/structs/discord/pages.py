import discord
import asyncio
from time import time
from enum import Enum
from discord.ext import commands
from typing import Optional, NoReturn
from lib.structs.discord.gitbot_embed import GitBotEmbed, GitBotCommandState
from lib.globs import Mgr


class EmbedPagesControl(Enum):
    BACK = '◀'
    STOP = '⏹'
    NEXT = '▶'


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

    def __init__(self, pages: list[GitBotEmbed | discord.Embed], timeout: int = 75, lifespan: int = 300):
        self.lifespan: float = lifespan
        self.timeout: int = timeout
        self.pages: list[GitBotEmbed | discord.Embed] = pages
        self.current_page: int = 0
        self.start_time: Optional[float] = None
        self.last_action_time: Optional[float] = None
        self.message: Optional[discord.Message] = None
        self.context: Optional[commands.Context] = None
        self.bot: Optional[commands.Bot] = None

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

    async def start(self, ctx: commands.Context) -> None:
        """
        Start the paginator in the passed context.

        :param ctx: The context to start the paginator in.
        """

        self._ensure_perms(ctx.channel)
        self.start_time = time()
        self.context: commands.Context = ctx
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
            self.current_page += 1
            self._action_time()
            await self.message.edit(embed=self.pages[self.current_page])

    async def previous_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self._action_time()
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

    def _action_time(self) -> None:
        self.last_action_time: float = time()

    def _ensure_perms(self, channel: discord.TextChannel) -> NoReturn:
        if not isinstance(channel, discord.DMChannel):
            permissions: discord.Permissions = channel.permissions_for(channel.guild.me)
            if not (permissions.administrator or (permissions.is_superset(discord.Permissions.all_channel())
                                                  and permissions.manage_messages)):
                raise EmbedPagesPermissionError

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
                              f'and time_since_last_action={self.time_since_last_action}')
                    await self.edit(GitBotCommandState.TIMEOUT)
                    break
                action: EmbedPagesControl = EmbedPagesControl(reaction.emoji)
                match action:
                    case EmbedPagesControl.BACK:
                        await self.previous_page()
                    case EmbedPagesControl.NEXT:
                        await self.next_page()
                    case EmbedPagesControl.STOP:
                        await self.edit(GitBotCommandState.CLOSED)
                        Mgr.debug('Stopping embed paginator loop - closed')
                        break
                Mgr.debug('Removing control reaction')
                await reaction.message.remove_reaction(reaction.emoji, user)
                await asyncio.sleep(0.555)
                Mgr.debug(f'Iteration complete with action {action.name}')
            else:
                Mgr.debug(f'Timeout with lifetime={self.lifetime} '
                          f'and time_since_last_action={self.time_since_last_action}')
                await self.edit(GitBotCommandState.TIMEOUT)
                break
