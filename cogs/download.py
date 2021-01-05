import discord
import io
from typing import Optional, Union
from discord.ext import commands
from ext.decorators import guild_available
from cfg import globals

Git = globals.Git


class Download(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client: commands.Bot = client
        self.emoji: str = '<:github:772040411954937876>'
        self.e: str = "<:ge:767823523573923890>"

    @commands.command(name='--download', aliases=['-download', 'download', '-dl'])
    @guild_available()
    @commands.max_concurrency(10, commands.BucketType.default, wait=False)
    @commands.cooldown(5, 30, commands.BucketType.user)
    async def download_command(self, ctx: commands.Context, repo: str):
        msg: discord.Message = await ctx.send(f"{self.emoji}  Give me a second while I download the file...")
        src_bytes: Optional[Union[bytes, bool]] = await Git.get_repo_zip(repo)
        if src_bytes is None:
            return await msg.edit(content=f"{self.e}  This repo **doesn't exist!**")
        elif src_bytes is False:
            return await msg.edit(
                content=f"{self.e}  That file is too big, **please download it directly here:**\nhttps://github.com/{repo}")
        io_obj: io.BytesIO = io.BytesIO(src_bytes)
        file: discord.File = discord.File(filename=f'{repo.replace("/", "-")}.zip', fp=io_obj)
        try:
            await ctx.send(file=file)
            await msg.edit(content=f'{self.emoji}  Here\'s the source code of **{repo}!**')
        except discord.errors.HTTPException:
            await msg.edit(
                content=f"{self.e} That file is too big, **please download it directly here:**\nhttps://github.com/{repo}")


def setup(client: commands.Bot) -> None:
    client.add_cog(Download(client))
