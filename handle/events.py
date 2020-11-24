import discord
from discord.ext import commands
from utils.explicit_checks import verify_send_perms
from ext.manager import Manager

mgr = Manager()


async def guild_text_channels(guild: discord.Guild):
    for channel in guild.text_channels:
        yield channel


class Events(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        invite = None
        receiver = None
        async for channel in guild_text_channels(guild):
            if await verify_send_perms(channel):
                receiver = channel
                invite = await receiver.create_invite()
                break
        embed = discord.Embed(
            color=0xefefef,
            title=None,
            description=":tada: **Hi! I'm GitHub.**\n\n**My prefix is** `git`\n**Use the command `git --help` to get started.\n\nIf you have any problems, [join the support server!](https://discord.gg/3e5fwpA)**\n\n**Now let's get this party started, shall we?**"
        )
        embed.set_thumbnail(url=self.client.user.avatar_url)
        embed.set_author(icon_url=self.client.user.avatar_url, name=self.client.user.name)
        embed.set_footer(text=f"© 2020 wulf, statch")

        embed_l = discord.Embed(
            title=f'{mgr.emojis["checkmark"]} Joined a new guild!',
            description=None,
            color=0xefefef,
            url=invite.url if invite is not None else "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        )
        owner = await self.client.fetch_user(guild.owner_id)
        embed_l.add_field(name='Name', value=str(guild))
        embed_l.add_field(name='Members', value=str(guild.member_count))
        embed_l.add_field(name='ID', value=f"`{str(guild.id)}`")
        embed_l.add_field(name='Owner', value=str(owner))
        embed_l.add_field(name='Created at', value=str(guild.created_at.strftime('%e, %b %Y')))
        embed_l.add_field(name='Channels', value=str(len(guild.channels) - len(guild.categories)))
        embed_l.set_footer(text=f"Now in {len(self.client.guilds)} guilds")

        print(f"Joined guild {guild} ({guild.id}) Now in {len(self.client.guilds)} guilds")

        channel = await self.client.fetch_channel(775042132054376448)  # Logging the join
        await channel.send(embed=embed_l)

        if receiver is not None: # Sending the join message
            await receiver.trigger_typing()
            await receiver.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        channel = self.client.get_channel(775042132054376448)
        print(f"Removed from guild {guild} ({guild.id}) Now in {len(self.client.guilds)} guilds")
        await channel.send(f"Removed from guild **{guild}** ({guild.id}) Now in {len(self.client.guilds)} guilds")

    @commands.Cog.listener()
    async def on_message(self, message) -> None:
        if self.client.user in message.mentions[:1] and len(message.content) < 23 and await verify_send_perms(message.channel):
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
