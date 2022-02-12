import discord
from datetime import date
from discord.ext import commands
from lib.globs import Mgr
from lib.structs import GitBotEmbed
from lib.structs.discord.context import GitBotContext
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
        embed: GitBotEmbed = GitBotEmbed(
            color=Mgr.c.rounded,
            description=f":tada: **Hi! I'm {self.bot.user.name}.**\n\n**My prefix is** `git`\n**Use the command `git "
                        f"--help` to get started.\n\nIf you have any problems, [join the support server!]("
                        f"https://discord.gg/3e5fwpA)**\n\n**Now let's get this party started, shall we?**",
            thumbnail=self.bot.user.avatar_url,
            author_name=self.bot.user.name,
            author_icon_url=self.bot.user.avatar_url,
            footer=f'© 2020-{date.today().year} wulf, statch'
        )
        embed_l: GitBotEmbed = await build_guild_embed(self.bot, guild)
        Mgr.log(f'Joined guild {guild} ({guild.id}) Now in {len(self.bot.guilds)} guilds', category='stats')

        if Mgr.env.production:
            await embed_l.send(await self.bot.fetch_channel(775042132054376448))

        if receiver is not None:  # Sending the join message
            await embed.send(receiver)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild) -> None:
        await Mgr.db.guilds.find_one_and_delete({'_id': guild.id})
        del Mgr.autoconv_cache[guild.id]
        embed_l: GitBotEmbed = await build_guild_embed(self.bot, guild, False)
        Mgr.log(f'Removed from guild {guild} ({guild.id}) Now in {len(self.bot.guilds)} guilds', category='stats')
        await embed_l.send(self.bot.get_channel(775042132054376448))

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.id == self.bot.user.id:
            return
        ctx: GitBotContext = await self.bot.get_context(message)
        if await Mgr.verify_send_perms(message.channel) and ctx.command is None:
            if all([self.bot.user in message.mentions, message.reference is None]):
                embed: GitBotEmbed = GitBotEmbed(
                    color=Mgr.c.rounded,
                    description=ctx.l.events.mention,
                    thumbnail=self.bot.user.avatar_url,
                    author_name=self.bot.user.name,
                    author_icon_url=self.bot.user.avatar_url,
                    author_url='https://statch.org/gitbot'
                )
                await embed.send(message.channel)
            else:
                handlers: tuple = (handle_codeblock_message, handle_link_message)
                for handler in handlers:
                    if await handler(ctx):
                        return
            if Mgr.getopt(message, 'reference.cached_message.author.id') == self.bot.user.id:
                await message.add_reaction('👀')
                return


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Events(bot))
