import discord
import io
from typing import Optional
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
    @commands.cooldown(5, 30, commands.BucketType.user)
    async def download_command(self, ctx: commands.Context, repo: str):
        src_bytes: Optional[bytes] = await Git.get_repo_zip(repo)
        if not src_bytes:
            return await ctx.send(f"{self.e} This repo **doesn't exist!**")
        io_obj: io.BytesIO = io.BytesIO(src_bytes)
        if io_obj.getbuffer().nbytes >= 47185920:  # abort upload if the file is bigger than 45mb
            return await ctx.send(
                f"{self.e} That file is too big, **please download it directly here:**\nhttps://github.com/{repo}")
        file: discord.File = discord.File(filename=f'{repo.replace("/", "-")}.zip', fp=io_obj)
        return await ctx.send(f'{self.emoji} Here\'s the source code of **{repo}!**', file=file)


def setup(client: commands.Bot) -> None:
    client.add_cog(Download(client))
