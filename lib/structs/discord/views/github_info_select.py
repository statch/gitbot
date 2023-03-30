import discord
import functools
from typing import TYPE_CHECKING
from string import Formatter
if TYPE_CHECKING:
    from ..context import GitBotContext



class GitHubInfoSelectMenu(discord.ui.Select):
    def __init__(self, ctx: 'GitBotContext', item_name: str, label_fmt: str, description_fmt: str, data: list[dict], callback) -> None:
        self.ctx: 'GitBotContext' = ctx
        self.data: list[dict] = data
        self.actual_callback = callback
        self.run_count: int = 0
        super().__init__(
            placeholder=ctx.l.views.select.github_info.placeholder.format(item_name),
            options=[
                discord.SelectOption(
                    label=label_fmt.format(**{key: ctx.bot.mgr.get_nested_key(item, key) for key in
                                              [fname for _, fname, _, _ in Formatter().parse(label_fmt) if fname]}),
                    description=self.ctx.bot.mgr.truncate(description_fmt.format(**{key: ctx.bot.mgr.get_nested_key(item, key) for key in
                                              [fname for _, fname, _, _ in Formatter().parse(description_fmt) if fname]}), 100),
                    # ^ truncated for max 100 allowed by discord, this field will typically be the title of the issue/pr-like item
                    value=str(i)
                ) for i, item in enumerate(data)
            ]
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        if interaction.user.id != self.ctx.author.id or self.disabled:
            return
        await interaction.response.defer()  # we ack the interaction and pretty much discard it
        self.ctx.send = functools.partial(self.ctx.send, reference=interaction.message, mention_author=False)  # reply
        await self.actual_callback(self.ctx, self.data[int(self.values[0])])  # call the callback that handles item
        self.run_count += 1
        if self.run_count >= 3:
            self.disabled = True
