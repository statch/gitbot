import discord
from discord.ext import commands
from utils.explicit_checks import verify_send_perms


async def guild_text_channels(guild: discord.Guild):
    for channel in guild.text_channels:
        yield channel


class Events(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        print(f"Joined guild {guild} ({guild.id}) Now in {len(self.client.guilds)} guilds")
        receiver = None
        wulf = await self.client.fetch_user(user_id=548803750634979340)
        await wulf.send(f"Joined guild **{guild}** ({guild.id}) Now in {len(self.client.guilds)} guilds")
        async for channel in guild_text_channels(guild):
            if await verify_send_perms(channel):
                receiver = channel
                break
        embed = discord.Embed(
            color=0xefefef,
            title=None,
            description=":tada: **Hi! I'm GitHub.**\n\n**My prefix is** `git`\n**Use the command `git --help` to get started.\n\nIf you have any problems, [join the support server!](https://discord.gg/3e5fwpA)**\n\n**Now let's get this party started, shall we?**"
        )
        embed.set_thumbnail(url=self.client.user.avatar_url)
        embed.set_author(icon_url=self.client.user.avatar_url, name=self.client.user.name)
        embed.set_footer(text=f"© 2020 wulf, Team Orion")
        if receiver is not None:
            await receiver.trigger_typing()
            await receiver.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        wulf = await self.client.fetch_user(user_id=548803750634979340)
        print(f"Removed from guild {guild} ({guild.id}) Now in {len(self.client.guilds)} guilds")
        await wulf.send(f"Joined guild **{guild}** ({guild.id}) Now in {len(self.client.guilds)} guilds")

    @commands.Cog.listener()
    async def on_message(self, message) -> None:
        if message.clean_content == f'<@!{self.client.user.id}>' and await verify_send_perms(message.channel):
            embed = discord.Embed(
                color=0xefefef,
                title=None,
                description=f":tada: **Hi! I'm GitHub.**\nMy prefix is `git`\nType `git --help` for a list of my commands."
            )
            embed.set_thumbnail(url=self.client.user.avatar_url)
            embed.set_author(icon_url=self.client.user.avatar_url, name=self.client.user.name)
            await message.channel.send(embed=embed)


def setup(client):
    client.add_cog(Events(client))
