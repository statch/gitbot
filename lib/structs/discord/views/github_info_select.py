import discord
import functools
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..context import GitBotContext


class GitHubInfoSelectMenu(discord.ui.Select):
    def __init__(self,
                 ctx: 'GitBotContext', item_name: str, label_fmt: str | tuple[str, tuple[Callable[[str], str], ...]],
                 description_fmt: str | tuple[str, tuple[Callable[[str], str], ...]], data: list[dict],
                 callback: Callable[..., Awaitable[['GitBotContext', dict], Any]] | Callable[['GitBotContext', dict], Any],
                 value_key: str | None = None) -> None:
        self.ctx: 'GitBotContext' = ctx
        self.data: list[dict] = data
        self.actual_callback = callback
        self.run_count: int = 0
        self.value_key: str | None = value_key
        if not isinstance(label_fmt, tuple):
            label_fmt = (label_fmt, ())
        if not isinstance(description_fmt, tuple):
            description_fmt = (description_fmt, ())
        super().__init__(
                placeholder=ctx.l.views.select.github_info.placeholder.format(item_name),
                options=[
                    discord.SelectOption(
                            label=self.ctx.bot.mgr.truncate(self.ctx.bot.mgr.advanced_format(label_fmt[0], item, label_fmt[1]), 100),
                            description=self.ctx.bot.mgr.truncate(self.ctx.bot.mgr.advanced_format(description_fmt[0], item, description_fmt[1]), 100),
                            # ^ truncated for max 100 allowed by discord
                            value=str(i) if value_key is None else ctx.bot.mgr.get_nested_key(item, value_key)
                    ) for i, item in enumerate(data)
                ]
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        if interaction.user.id != self.ctx.author.id or self.disabled:
            return
        self.ctx.send = functools.partial(self.ctx.send, reference=interaction.message, mention_author=False)  # reply
        await self.ctx.bot.mgr.just_run(self.actual_callback, self.ctx,
                                        (self.data[int(self.values[0])] if self.value_key is None else
                                         self.ctx.bot.mgr.get_by_key_from_sequence(self.data,
                                                                                   self.value_key, self.values[0])))
        self.run_count += 1
        if self.run_count >= 3:
            self.disabled = True
        await interaction.response.defer()


class GitHubInfoSelectView(discord.ui.View):
    def __init__(self,
                 ctx: 'GitBotContext', item_name: str, label_fmt: str, description_fmt: str, data: list[dict],
                 callback: Callable[..., Awaitable[['GitBotContext', dict], Any]] | Callable[['GitBotContext', dict], Any],
                 value_key: str | None = None, **kwargs) -> None:
        super().__init__(**kwargs)

        self.add_item(GitHubInfoSelectMenu(ctx, item_name, label_fmt, description_fmt, data, callback, value_key))
