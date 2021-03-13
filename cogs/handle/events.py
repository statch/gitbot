import discord
from discord.ext import commands

from core.globs import Mgr
from ext.explicit_checks import verify_send_perms


async def guild_text_channels(guild: discord.Guild):
    for channel in guild.text_channels:
        yield channel


class Events(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot

    async def build_guild_embed(
        self, guild: discord.Guild, state: bool = True
    ) -> discord.Embed:
        if state:
            title: str = f'{Mgr.emojis["checkmark"]}  Joined a new guild!'
            color: int = 0x33BA7C
        else:
            title: str = f'{Mgr.emojis["failure"]}  Removed from a guild.'
            color: int = 0xDA4353

        embed = discord.Embed(
            title=title,
            description=None,
            color=color,
        )
        owner = await self.bot.fetch_user(guild.owner_id)
        embed.add_field(name="Name", value=str(guild))
        embed.add_field(name="Members", value=str(guild.member_count))
        embed.add_field(name="ID", value=f"`{str(guild.id)}`")
        embed.add_field(name="Owner", value=str(owner))
        embed.add_field(
            name="Created at", value=str(guild.created_at.strftime("%e, %b %Y"))
        )
        embed.add_field(
            name="Channels", value=str(len(guild.channels) - len(guild.categories))
        )
        embed.set_footer(text=f"Now in {len(self.bot.guilds)} guilds")
        embed.set_thumbnail(url=guild.icon_url)

        return embed

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild) -> None:
        receiver = None
        async for channel in guild_text_channels(guild):
            if await verify_send_perms(channel):
                receiver = channel
                break
        embed = discord.Embed(
            color=0xEFEFEF,
            title=None,
            description=f":tada: **Hi! I'm {self.bot.user.name}.**\n\n**My prefix is** `git`\n**Use the command `git --help` to get started.\n\nIf you have any problems, [join the support server!](https://discord.gg/3e5fwpA)**\n\n**Now let's get this party started, shall we?**",
        )
        embed.set_thumbnail(url=self.bot.user.avatar_url)
        embed.set_author(icon_url=self.bot.user.avatar_url, name=self.bot.user.name)
        embed.set_footer(text=f"© 2020 wulf, statch")

        embed_l: discord.Embed = await self.build_guild_embed(guild)

        print(f"Joined guild {guild} ({guild.id}) Now in {len(self.bot.guilds)} guilds")

        # Logging the join
        channel = await self.bot.fetch_channel(775042132054376448)
        await channel.send(embed=embed_l)

        if receiver is not None:  # Sending the join message
            await receiver.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild) -> None:
        embed_l: discord.Embed = await self.build_guild_embed(guild, False)
        channel = self.bot.get_channel(775042132054376448)
        print(
            f"Removed from guild {guild} ({guild.id}) Now in {len(self.bot.guilds)} guilds"
        )
        await channel.send(embed=embed_l)

    @commands.Cog.listener()
    async def on_message(self, message) -> None:
        can_send: bool = await verify_send_perms(message.channel)
        if all(
            [self.bot.user in message.mentions[:1], len(message.content) < 23, can_send]
        ):
            embed = discord.Embed(
                color=0xEFEFEF,
                title=None,
                description=f":tada: **Hi! I'm {self.bot.user.name}.**\nMy prefix is `git`\nType `git --help` for a list of my commands.",
            )
            embed.set_thumbnail(url=self.bot.user.avatar_url)
            embed.set_author(icon_url=self.bot.user.avatar_url, name=self.bot.user.name)
            await message.channel.send(embed=embed)


def setup(bot):
    bot.add_cog(Events(bot))
