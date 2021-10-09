import discord
from discord.ext import commands
from lib.globs import Mgr
from .event_tools import build_guild_embed, handle_codeblock_message, handle_link_message  # noqa


async def guild_text_channels(guild: discord.Guild):
    for channel in guild.text_channels:
        yield channel


class Events(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild) -> None:
        receiver = None
        async for channel in guild_text_channels(guild):
            if await Mgr.verify_send_perms(channel):
                receiver = channel
                break
        embed = discord.Embed(
            color=Mgr.c.rounded,
            description=f":tada: **Hi! I'm {self.bot.user.name}.**\n\n**My prefix is** `git`\n**Use the command `git "
                        f"--help` to get started.\n\nIf you have any problems, [join the support server!]("
                        f"https://discord.gg/3e5fwpA)**\n\n**Now let's get this party started, shall we?**"
        )
        embed.set_thumbnail(url=self.bot.user.avatar_url)
        embed.set_author(icon_url=self.bot.user.avatar_url, name=self.bot.user.name)
        embed.set_footer(text=f"© 2020 wulf, statch")

        embed_l: discord.Embed = await build_guild_embed(self.bot, guild)

        Mgr.log(f'Joined guild {guild} ({guild.id}) Now in {len(self.bot.guilds)} guilds', category='stats')

        if Mgr.env.production:
            channel = await self.bot.fetch_channel(775042132054376448)  # Logging the join
            await channel.send(embed=embed_l)

        if receiver is not None:  # Sending the join message
            await receiver.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild) -> None:
        await Mgr.db.guilds.find_one_and_delete({'_id': guild.id})
        del Mgr.autoconv_cache[guild.id]
        embed_l: discord.Embed = await build_guild_embed(self.bot, guild, False)
        channel = self.bot.get_channel(775042132054376448)
        Mgr.log(f"Removed from guild {guild} ({guild.id}) Now in {len(self.bot.guilds)} guilds", category='stats')
        await channel.send(embed=embed_l)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.id == self.bot.user.id:
            return
        ctx: commands.Context = await self.bot.get_context(message)
        if await Mgr.verify_send_perms(message.channel) and ctx.command is None:
            await Mgr.enrich_context(ctx)
            if all([self.bot.user in message.mentions, message.reference is None]):
                embed: discord.Embed = discord.Embed(
                    color=Mgr.c.rounded,
                    description=ctx.l.events.mention
                )
                embed.set_thumbnail(url=self.bot.user.avatar_url)
                embed.set_author(icon_url=self.bot.user.avatar_url, name=self.bot.user.name)
                await message.channel.send(embed=embed)
            else:
                handlers: tuple = (handle_codeblock_message, handle_link_message)
                for handler in handlers:
                    if await handler(ctx):
                        break


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Events(bot))
