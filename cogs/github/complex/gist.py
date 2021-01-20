import discord
import datetime
from asyncio import TimeoutError
from discord.ext import commands
from core import bot_config
from ext.manager import Manager

Git = bot_config.Git
mgr = Manager()


class Gist(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot
        self.e: str = "<:ge:767823523573923890>"

    @commands.command(name='gist', aliases=['-gist', '--gist', 'gists', '-gists', '--gists'])
    @commands.cooldown(10, 30, commands.BucketType.user)
    async def gist_command(self, ctx: commands.Context, user: str) -> None:
        data: dict = await Git.get_user_gists(user)
        if data is None:
            await ctx.send(f'{self.e}  This user **doesn\'t exist!**')
            return
        embed: discord.Embed = discord.Embed(
            color=0xefefef,
            title=f'{user}\'s gists',
            description=None,
            url=data['url']
        )

        await ctx.send(embed=embed)

        try:
            msg: discord.Message = await self.bot.wait_for('message',
                                                           check=lambda m: (m.channel.id == ctx.channel.id
                                                                            and m.author.id == ctx.author.id),
                                                           timeout=30)
        except TimeoutError:
            return

        await ctx.send(embed=await self.build_gist_embed(data, int(msg.clean_content)))

    async def build_gist_embed(self, data: dict, index: int) -> discord.Embed:
        gist: dict = data['gists']['nodes'][index - 1 if index != 0 else 1]
        embed = discord.Embed(
            color=await self.get_color_from_files(gist['files']),
            title=gist['description'],
            description=None,
            url=gist['url']
        )

        created_at: str = f"Created by [{data['login']}]({data['url']}) on {datetime.datetime.strptime(gist['createdAt'], '%Y-%m-%dT%H:%M:%SZ').strftime('%e, %b %Y')}\n"
        updated_at: str = f"Last updated at {datetime.datetime.strptime(gist['updatedAt'], '%Y-%m-%dT%H:%M:%SZ').strftime('%e, %b %Y')}\n"
        stargazers = f"Has [{gist['stargazerCount']} stargazers]({gist['url']}/stargazers)" if gist[
                                                                                                   'stargazerCount'] != 1 else f"Has [one stargazer]({gist['url']}/stargazers)"
        if gist['stargazerCount'] == 0:
            stargazers = "Has no stargazers"
        comment_count = gist['comments']['totalCount']
        comments = f"and [{comment_count} comments]({gist['url']})" if comment_count != 1 else f"and [one comment]({gist['url']})"
        if gist['stargazerCount'] == 0:
            comments = "and no comments"

        stargazers_and_comments = f'{stargazers} and {comments}'
        info: str = f'{created_at}{updated_at}{stargazers_and_comments}'
        embed.add_field(name=":mag_right: Info:", value=info, inline=False)

        return embed

    async def get_color_from_files(self, files: list) -> int:
        extensions = [f['extension'] for f in files]
        most_common = await mgr.get_most_common(extensions)
        if most_common in ['.md', '']:
            return 0xefefef
        for file in files:
            if file['extension'] == most_common and file['language'] is not None:
                return int(file['language']['color'][1:], 16)
        return 0xefefef


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Gist(bot))
