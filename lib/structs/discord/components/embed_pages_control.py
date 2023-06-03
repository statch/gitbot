import discord
import asyncio
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..context import GitBotContext
    from ..pages import EmbedPages


class EmbedPagesControlView(discord.ui.View):
    def __init__(self, pages: 'EmbedPages'):
        super().__init__()
        self.context: 'GitBotContext' = pages.context
        self.pages: 'EmbedPages' = pages


    @discord.ui.button(custom_id='first', emoji='⏮', style=discord.ButtonStyle.grey)
    async def to_first_page(self, interaction: discord.Interaction, _):
        await interaction.response.defer()
        if self.pages.current_page != 1:
            await self.pages.to_first_page()

    @discord.ui.button(custom_id='prev', emoji='◀', style=discord.ButtonStyle.grey)
    async def prev_page(self, interaction: discord.Interaction, _):
        await interaction.response.defer()
        if self.pages.current_page > 0:
            await self.pages.previous_page()

    @discord.ui.button(custom_id='next', emoji='▶', style=discord.ButtonStyle.grey)
    async def next_page(self, interaction: discord.Interaction, _):
        await interaction.response.defer()
        if self.pages.current_page + 1 < len(self.pages):
            await self.pages.next_page()

    @discord.ui.button(custom_id='last', emoji='⏭', style=discord.ButtonStyle.grey)
    async def to_last_page(self, interaction: discord.Interaction, _):
        await interaction.response.defer()
        if self.pages.current_page != len(self.pages) - 1:
            await self.pages.to_last_page()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if self.pages.time_since_last_action < 0.75:
            await asyncio.sleep(0.75 - self.pages.time_since_last_action)
        return interaction.user.id == self.context.author.id and not self.pages.should_die
