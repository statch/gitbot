import discord
from typing import TYPE_CHECKING, Optional
from lib.structs.enums import GitBotCommandState

if TYPE_CHECKING:
    from lib.structs import GitBotContext, GitBotEmbed


class ConfirmationView(discord.ui.View):
    def __init__(self, context: 'GitBotContext', embed: 'GitBotEmbed', *, timeout: float = 45.0):
        super().__init__(timeout=timeout)
        self.context: 'GitBotContext' = context
        self.embed: Optional['GitBotEmbed'] = embed
        self.value: bool | None = None
        self.context_to_edit: Optional['GitBotContext'] = None

    @discord.ui.button(custom_id='confirmation_yes', emoji='<:checkmark:770244084727283732>', style=discord.ButtonStyle.green)
    async def yes(self, interaction: discord.Interaction, _):
        await interaction.response.defer()
        self.value = True
        self.stop()
        await self.embed.edit_with_state(self.context_to_edit, GitBotCommandState.SUCCESS)

    @discord.ui.button(custom_id='confirmation_no', emoji='<:failure:770244076896256010>', style=discord.ButtonStyle.red)
    async def no(self, interaction: discord.Interaction, _):
        await interaction.response.defer()
        self.value = False
        self.stop()
        await self.embed.edit_with_state(self.context_to_edit, GitBotCommandState.FAILURE)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.context.author.id

    async def on_timeout(self) -> None:
        await self.embed.edit_with_state(self.context_to_edit, GitBotCommandState.TIMEOUT)
