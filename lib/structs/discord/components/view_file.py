import io
import discord
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lib.structs.discord.bot import GitBot
    from lib.structs.discord.context import GitBotContext


class ViewFileButton(discord.ui.Button):
    def __init__(self, ctx: 'GitBotContext', label: str, file_url: str, emoji: str | None = None,
                 style: discord.ButtonStyle = discord.ButtonStyle.gray):
        if style == discord.ButtonStyle.link:
            raise Exception('ButtonStyle cannot be "link" due to callbacks being necessary')
        emoji: str = emoji if emoji else ctx.bot.mgr.e.file
        self.bot: 'GitBot' = ctx.bot
        self.file_url: str = file_url
        self.filetype: str = file_url.split('.')[-1]
        self._file: io.BytesIO | None = None
        self._filename: str | None = None
        self._used_by: set = set()
        super().__init__(label=label, emoji=emoji, style=style)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id in self._used_by:
            self.bot.logger.debug(f'File from {self.file_url} already sent to {interaction.user} ({interaction.user.id})')
            return
        if self._file is None:
            self.bot.logger.debug(f'Fetching file from {self.file_url}...')
            if (res := await self.bot.session.get(self.file_url)).status != 200:
                return
            if (file := io.BytesIO(await res.content.read())).getbuffer().nbytes > int(7.85 * (1024 ** 2)):
                return
            self._file: io.BytesIO = file
            self._filename: str = f'{self.file_url.split("/")[2].replace(".", "_")}.{self.filetype}'
        self._file.seek(0)  # reset file pointer from potential previous reads by discord.py
        self._used_by.add(interaction.user.id)
        await interaction.response.send_message(file=discord.File(self._file, filename=self._filename), ephemeral=True)
