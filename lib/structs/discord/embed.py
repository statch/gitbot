"""
Custom Discord embed interface implementation for GitBot
~~~~~~~~~~~~~~~~~~~
A non-native replacement for the embed object provided in discord.ext.commands
:copyright: (c) 2020-present statch
:license: CC BY-NC-ND 4.0, see LICENSE for more details.
"""

import enum
import discord
import asyncio
import functools
import operator
from lib.utils.regex import MARKDOWN_EMOJI_RE
from typing import Callable, Optional, Awaitable, Any, TYPE_CHECKING
from lib.structs.proxies.dict_proxy import DictProxy
if TYPE_CHECKING:
    from lib.structs.discord.context import GitBotContext
from lib.typehints import EmbedLike

__all__: tuple = ('GitBotEmbed', 'GitBotCommandState')


@enum.unique
class GitBotCommandState(enum.Enum):
    FAILURE: int = 0
    CONTINUE: int = 1
    SUCCESS: int = 2
    TIMEOUT: int = 3
    CLOSED: int = 4


GitBotEmbedResponseCallback = Callable[..., Awaitable[tuple[GitBotCommandState | Optional[tuple[Any, ...] | Any],
                                                            GitBotCommandState]]]


class GitBotEmbed(discord.Embed):
    """
    A subclass of :class:`discord.Embed` with added GitBot™ functionality.
    Takes in the same arguments as the native implementation of Embed + additional ones in the signature.
    """

    def __init__(self,
                 footer: str = discord.Embed.Empty,
                 footer_icon_url: str = discord.Embed.Empty,
                 thumbnail: str = discord.Embed.Empty,
                 author_name: str = '',
                 author_url: str = discord.Embed.Empty,
                 author_icon_url: str = discord.Embed.Empty,
                 **kwargs):
        kwargs.setdefault('color', 0x2F3136)
        super().__init__(**kwargs)
        self.set_footer(text=footer, icon_url=footer_icon_url)
        self.set_thumbnail(url=thumbnail)
        if author_name:
            self.set_author(name=author_name, url=author_url, icon_url=author_icon_url)

    @classmethod
    def from_locale_resource(cls, ctx: 'GitBotContext', resource: str, **kwargs) -> 'GitBotEmbed':
        """
        Creates an embed from a locale resource.

        :param ctx: The context for localization of the embed
        :param resource: The locale resource to use
        :param args: The arguments to pass to the embed
        :param kwargs: The keyword arguments to pass to the embed
        :return: The created embed
        """

        resource: DictProxy = functools.reduce(operator.getitem, resource.split(), ctx.l)  # noqa: type valid
        kwargs.setdefault('title', resource.get('title', discord.Embed.Empty))
        kwargs.setdefault('description', resource.get('description', discord.Embed.Empty))
        kwargs.setdefault('footer', resource.get('footer', discord.Embed.Empty))
        embed: 'GitBotEmbed' = cls(**kwargs)
        if 'fields' in resource:
            for field in resource['fields']:
                embed.add_field(name=field['name'], value=field['value'], inline=field.get('inline', False))
        return embed

    async def send(self, messageable: discord.abc.Messageable, *args, **kwargs) -> discord.Message:
        return await messageable.send(embed=self, *args, **kwargs)

    async def edit_with_state(self, ctx: 'GitBotContext', state: int) -> None:
        if ctx.author.id is ctx.guild.me.id:
            _embed: EmbedLike = ctx.message.embeds[0] if ctx.message.embeds else None
            if _embed:
                if state is GitBotCommandState.SUCCESS:
                    self._input_with_timeout_update(0x57F287,
                                                    '<:checkmark:770244084727283732>',
                                                    ctx.l.generic.completed,
                                                    _embed)
                elif state is GitBotCommandState.FAILURE:
                    self._input_with_timeout_update(0xED4245,
                                                    '<:failure:770244076896256010>',
                                                    ctx.l.generic.failure,
                                                    _embed)
                elif state is GitBotCommandState.TIMEOUT:
                    self._input_with_timeout_update(0xFEE75C, ':warning:', ctx.l.generic.inactive, _embed)
                await ctx.message.edit(embed=_embed)

    def _input_with_timeout_update(self,
                                   color: int,
                                   emoji_name: str,
                                   footer: str,
                                   to_edit: Optional[EmbedLike] = None) -> None:
        to_edit: EmbedLike = self if not to_edit else to_edit
        to_edit.colour = color
        to_edit.title = f'{emoji_name}  ' + MARKDOWN_EMOJI_RE.sub('', to_edit.title).strip()
        to_edit.set_footer(text=footer)

    async def input_with_timeout(self,
                                 ctx: 'GitBotContext',
                                 event: str,
                                 timeout: int,
                                 timeout_check: Callable[[Any], bool],
                                 response_callback: GitBotEmbedResponseCallback,
                                 init_message: Optional[discord.Message] = None,
                                 with_antispam: bool = True,
                                 antispam_threshold: int = 5,
                                 *args,
                                 **kwargs) -> tuple[Optional[discord.Message], Optional[tuple[Any, ...] | Any]]:
        """
        Run a simple timeout loop.

        This method is used to clean up otherwise spaghetti code and unify embed behavior throughout the client.

        It operates on a simple API structure based around the response callback:

        -   The callback is expected to accept a message (the init one) and a tuple of the event's returns
        -   It's expected to return a :class:`GitBotCommandState` flag and an optional tuple of arguments
            that are passed up to the root call to prevent the need to do stuff like double validation
        -   **The flag signifies whether or not the internal loop should end its otherwise perpetual execution**

        :param ctx: The context to use
        :param event: The event to listen for
        :param timeout: The timeout to use
        :param timeout_check: The check for the timeout, typically author and channel wide
        :param response_callback: The aforesaid callback
        :param init_message: An existing message to use as the initial one instead of sending a new one
        :param with_antispam: Whether to accept only a certain amount of GitBotCommandState.CONTINUEs
                              before a GitBotCommandState.FAILURE is returned
        :param antispam_threshold: The amount of permitted CONTINUE states
        :return: Optional message and optional callback returns
        """

        if not init_message:
            init_message: discord.Message = await self.send(ctx)

        new_ctx: 'GitBotContext' = await ctx.bot.get_context(init_message)
        missing_slots: set = set(dir(ctx)) ^ set(dir(new_ctx))
        for slot in missing_slots:
            setattr(new_ctx, slot, getattr(ctx, slot))
        ctx: 'GitBotContext' = new_ctx
        antispam: int = 0

        try:
            while True:
                event_data = await ctx.bot.wait_for(event, check=timeout_check, timeout=timeout)
                callback_result = await response_callback(init_message, event_data, *args, **kwargs)
                state: GitBotCommandState = (callback_result if not isinstance(callback_result, tuple)
                                             else callback_result[0])
                return_args = None if not isinstance(callback_result, tuple) else callback_result[1:]
                if antispam >= antispam_threshold-1 and with_antispam:
                    state: int = GitBotCommandState.FAILURE
                if state is GitBotCommandState.CONTINUE:
                    antispam += 1
                    continue
                await self.edit_with_state(ctx, state)
                return event_data, return_args if return_args is None else return_args[0]
        except asyncio.TimeoutError:
            await self.edit_with_state(ctx, GitBotCommandState.TIMEOUT)
        return None, None

    async def confirmation(self, ctx: 'GitBotContext', callback: GitBotEmbedResponseCallback) -> bool:
        """
        Run a prompt to confirm something.

        :param ctx: The invocation context
        :param callback: The callback to use (same as in :meth:`input_with_timeout`)
        :return: Whether the user confirmed
        """

        initial_message: discord.Message = await self.send(ctx)
        await initial_message.add_reaction('<:checkmark:770244084727283732>')
        await initial_message.add_reaction('<:failure:770244076896256010>')
        result: tuple[Optional[discord.Message], Optional[tuple[Any, ...] | Any]] = await self.input_with_timeout(
            ctx=ctx,
            event='reaction_add',
            timeout=30,
            timeout_check=lambda r, m: all([r.custom_emoji,
                                            r.emoji.id in (770244076896256010, 770244084727283732),
                                            m.id == ctx.author.id,
                                            r.message.id == initial_message.id]),
            response_callback=callback,
            init_message=initial_message
        )
        if (result and result[0] and isinstance(result[0][0], discord.Reaction)
                and result[0][0].custom_emoji and result[0][0].emoji.id == 770244084727283732):
            return True
        return False
