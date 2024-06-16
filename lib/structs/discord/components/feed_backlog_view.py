import discord
from typing import TYPE_CHECKING, Callable, Any, Coroutine

if TYPE_CHECKING:
    from lib.typehints.db.guild.release_feed import ReleaseFeedRepo, ReleaseFeedItem
    from lib.structs import GitBotContext

__all__: tuple = ('ReleaseFeedBacklogView',)


class ReleaseFeedBacklogView(discord.ui.View):
    def __init__(self, ctx: 'GitBotContext', rfi: 'ReleaseFeedItem', rfr: 'ReleaseFeedRepo', timeout: int = 180):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.rfi, self.rfr = rfi, rfr
        self.add_item(_FetchReleaseFeedBacklogButton(ctx=ctx))
        self.fetch_btn = self.children[0]


class _FetchReleaseFeedBacklogButton(discord.ui.Button):
    view: 'ReleaseFeedBacklogView'

    def __init__(self, ctx: 'GitBotContext'):
        self.ctx = ctx
        super().__init__(label=self.ctx.l.config.feed.repo.backlog.button.label, row=0)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.ctx.author.id or self.disabled:
            return

        async def _closing_hook():  # close everything up so that we don't get double interactions
            self.disabled = True
            await interaction.message.edit(view=None)
            await interaction.delete_original_response()

        await interaction.response.send_message(self.ctx.l.config.feed.repo.backlog.how_many, ephemeral=True,
                                                view=_ReleaseFeedBacklogWantedView(self.ctx, self.view.rfi,
                                                                                   self.view.rfr, self.view,
                                                                                   _closing_hook))


class _ReleaseFeedBacklogWantedView(discord.ui.View):
    def __init__(self, ctx: 'GitBotContext', rfi: 'ReleaseFeedItem', rfr: 'ReleaseFeedRepo',
                 orig_view: 'ReleaseFeedBacklogView', after_hook: Callable[..., Coroutine[Any, Any, None]]):
        super().__init__(timeout=orig_view.timeout)
        self.ctx = ctx
        self.rfi, self.rfr = rfi, rfr
        self.orig_view = orig_view
        self.after_hook = after_hook
        self.add_item(_FetchReleaseFeedBacklogSelectMenu(ctx=ctx))


class _FetchReleaseFeedBacklogSelectMenu(discord.ui.Select):
    view: '_ReleaseFeedBacklogWantedView'

    def __init__(self, ctx: 'GitBotContext'):
        self.ctx = ctx
        options: list[discord.SelectOption] = [
            discord.SelectOption(description=self.ctx.l.config.feed.repo.backlog.select.options.one,
                                 emoji=self.ctx.bot.mgr.e.digits.pixel.one, label='1', value='1'),
            discord.SelectOption(description=self.ctx.l.config.feed.repo.backlog.select.options.five,
                                 emoji=self.ctx.bot.mgr.e.digits.pixel.five, label='5', value='5'),
            discord.SelectOption(description=self.ctx.l.config.feed.repo.backlog.select.options.ten,
                                 emoji=self.ctx.bot.mgr.e.digits.pixel.ten, label='10', value='10')
        ]

        super().__init__(placeholder=self.ctx.l.config.feed.repo.backlog.select.placeholder, options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(self.ctx.bot.mgr.e.dot_sep + '  ' +
                                                self.ctx.l.config.feed.repo.backlog.fetching, ephemeral=True)
        n: int = await self.view.ctx.bot.mgr.handle_backlog_request(self.ctx, self.view.rfi, self.view.rfr,
                                                                    int(self.values[0]))
        self.disabled = True
        await self.view.after_hook()
        if n:
            await interaction.edit_original_response(
                content=(self.ctx.bot.mgr.e.checkmark + '  ' +
                         self.ctx.l.config.feed.repo.backlog.fetched.format(n, '<#' + str(self.view.rfi['cid']) + '>')),
                view=None)
        else:
            await interaction.edit_original_response(
                content=f'{self.ctx.bot.mgr.e.circle_yellow}  {self.ctx.l.config.feed.repo.backlog.no_backlog}',
                view=None)
