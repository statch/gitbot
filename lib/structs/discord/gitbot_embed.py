import enum
import discord
import asyncio
from lib.utils.regex import MD_EMOJI_RE
from discord.ext import commands
from typing import Callable, Optional, Awaitable, Any, Union
from lib.typehints import EmbedLike

__all__: tuple = ('GitBotEmbed', 'GitBotCommandState')


@enum.unique
class GitBotCommandState(enum.Enum):
    FAILURE: int = 0
    CONTINUE: int = 1
    SUCCESS: int = 2
    TIMEOUT: int = 3


class GitBotEmbed(discord.Embed):
    """
    A subclass of :class:`discord.Embed` with added GitBot™ functionality.
    Takes in the same arguments as the native implementation of Embed + additional ones in the signature.
    """

    def __init__(self,
                 footer=discord.Embed.Empty,
                 footer_icon_url=discord.Embed.Empty,
                 thumbnail=discord.Embed.Empty,
                 **kwargs):
        kwargs.setdefault('color', 0x2F3136)
        super().__init__(**kwargs)
        self.set_footer(text=footer, icon_url=footer_icon_url)
        self.set_thumbnail(url=thumbnail)

    async def send(self, ctx: commands.Context, *args, **kwargs) -> discord.Message:
        return await ctx.send(embed=self, *args, **kwargs)

    async def edit_with_state(self, ctx: commands.Context, state: GitBotCommandState) -> None:
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
        to_edit.title = f'{emoji_name}  ' + MD_EMOJI_RE.sub('', to_edit.title).strip()
        to_edit.set_footer(text=footer)

    async def input_with_timeout(self,
                                 ctx: commands.Context,
                                 event: str,
                                 timeout: int,
                                 timeout_check: Callable[[Any], bool],
                                 response_callback: Callable[..., Awaitable[Union[tuple[GitBotCommandState,
                                                                                        Optional[Union[tuple[Any, ...],
                                                                                                       Any]]],
                                                                                  GitBotCommandState]]],
                                 init_message: Optional[discord.Message] = None,
                                 *args,
                                 **kwargs) -> tuple[Optional[discord.Message], Optional[Union[tuple[Any, ...], Any]]]:
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
        :return: Optional message and optional callback returns
        """

        if not init_message:
            init_message: discord.Message = await self.send(ctx)

        try:
            while True:
                event_data = await ctx.bot.wait_for(event, check=timeout_check, timeout=timeout)
                callback_result = await response_callback(init_message, event_data, *args, **kwargs)
                state: GitBotCommandState = (callback_result if not isinstance(callback_result, tuple)
                                             else callback_result[0])
                return_args = None if not isinstance(callback_result, tuple) else callback_result[1:]
                if state is GitBotCommandState.CONTINUE:
                    continue
                await self.edit_with_state(ctx, state)
                await init_message.edit(embed=self)
                return event_data, return_args if return_args is None else return_args[0]
        except asyncio.TimeoutError:
            await self.edit_with_state(ctx, GitBotCommandState.TIMEOUT)  # noqa
            await init_message.edit(embed=self)
        return None, None
