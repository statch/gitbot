import discord
from discord.ext import commands
from ext.decorators import guild_available
import datetime

start_time = datetime.datetime.utcnow()


class BotInfo(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.emoji: str = '<:github:772040411954937876>'
        self.s: str = "<:gs:767809543815954463>"

    @commands.command(name='--uptime', aliases=['--up'], brief="Display's the Bot's uptime")
    @commands.cooldown(15, 30, commands.BucketType.member)
    @guild_available()
    async def uptime_command(self, ctx) -> None:
        now = datetime.datetime.utcnow()
        delta = now - start_time
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        days, hours = divmod(hours, 24)
        if days:
            time_format = "**{d}** days, **{h}** hours, **{m}** minutes, and **{s}** seconds."
        else:
            time_format = "**{h}** hours, **{m}** minutes, and **{s}** seconds."
        uptime_stamp = time_format.format(d=days, h=hours, m=minutes, s=seconds)
        embed = discord.Embed(
            color=0xefefef,
            title=None,
            description=f"{self.s}  **I have been online for:**\n{uptime_stamp}"
        )
        await ctx.send(embed=embed)

    @commands.command(name='--ping', brief="Display's the Bot's ping", aliases=["--p"])
    @commands.cooldown(15, 30, commands.BucketType.member)
    @guild_available()
    async def ping_command(self, ctx) -> None:
        embed = discord.Embed(
            color=0xefefef,
            title=None,
            description=f"{self.s}  **My ping is:**\n**{round(self.client.latency * 1000)}** milliseconds"
        )
        await ctx.send(embed=embed)

    @commands.command(name='--privacy', brief="Display's the Bot's privacy policy")
    @commands.cooldown(15, 30, commands.BucketType.member)
    @guild_available()
    async def privacy_policy(self, ctx):
        embed = discord.Embed(
            color=0xefefef,
            title=f"{self.emoji}  Privacy Policy",
            description=None
        )
        embed.add_field(name="What is stored?", inline=False,
                        value="The only data stored are your User ID and quick access users, repos and orgs.")
        embed.add_field(name="How is all this used anyway?", inline=False,
                        value="It's used to provide storage for your saved users, repos and organizations, your User "
                              "ID is essential for the Bot to know, what data is yours.")
        embed.add_field(name="Who has access to this data?", inline=False,
                        value="Only the Bot's developer has access, no one else. Your data isn't viewed or accessed "
                              "in any way unless it's required to provide the service.")
        embed.add_field(name="How can I get rid of this stored data?", inline=False,
                        value="You can do that very easily by using the `git config -delete` command!")
        embed.add_field(name="Who wrote this and can this be changed?", inline=False,
                        value="This privacy policy was written by [wulf](https://dsc.bio/wulf), the Bot's developer, "
                              "and yes, all of this is subject to change in the future.")
        await ctx.send(embed=embed)

    @commands.command(name='--invite', aliases=['invite', '-invite'])
    @commands.cooldown(15, 30, commands.BucketType.member)
    @guild_available()
    async def invite_command(self, ctx):
        embed = discord.Embed(
            color=0xefefef,
            title=f'{self.emoji}  Invite GitHub to your server!',
            description="[Invite GitHub](https://discord.com/oauth2/authorize?client_id=761269120691470357&scope=bot&permissions=67488832) | [Support Server](https://discord.gg/3e5fwpA)"
        )
        embed.set_author(icon_url=self.client.user.avatar_url, name=self.client.user.name)
        await ctx.send(embed=embed)


def setup(client):
    client.add_cog(BotInfo(client))
