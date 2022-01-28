import discord
import asyncio
from discord.ext import commands
from lib.globs import Git, Mgr
from typing import Optional
from lib.utils.decorators import gitbot_command 
from lib.typehints import GitHubUser
from lib.structs.discord.context import GitBotContext

DISCORD_MD_LANGS: tuple = ('java', 'js', 'py', 'css', 'cs', 'c',
                           'cpp', 'html', 'php', 'json', 'xml', 'yml',
                           'nim', 'md', 'go', 'kt')


class Gist(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot

    @gitbot_command(name='gist', aliases=['gists'])
    @commands.cooldown(10, 30, commands.BucketType.user)
    async def gist_command(self,
                           ctx: GitBotContext,
                           user: GitHubUser,
                           ind: Optional[int | str] = None) -> None:
        ctx.fmt.set_prefix('gist')
        data: dict = await Git.get_user_gists(user)
        if not data:
            await ctx.error(ctx.l.generic.nonexistent.user.base)
            return
        if (gists := len(data['gists']['nodes'])) < 2:
            if gists == 0:
                await ctx.error(ctx.l.generic.nonexistent.gist)
            else:
                await ctx.send(embed=await self.build_gist_embed(ctx, data, 1,
                                                                 footer=ctx.l.gist.no_list))
            return

        def gist_url(gist: dict) -> str:
            if not gist['description']:
                return gist['url']
            desc = gist["description"] if len(gist["description"]) < 70 else gist["description"][:67] + '...'
            return f'[{desc}]({gist["url"]})'

        gist_strings: list = [f'{Mgr.e.square}**{ind + 1} |** {gist_url(gist)}' for ind, gist in
                              enumerate(data['gists']['nodes'])]

        embed: discord.Embed = discord.Embed(
            color=Mgr.c.rounded,
            title=ctx.fmt('title', user),
            description='\n'.join(gist_strings),
            url=data['url']
        )

        embed.set_footer(text=ctx.fmt('footer', user))

        base_msg: discord.Message = await ctx.send(embed=embed)

        def validate_index(index: int | str) -> tuple[bool, Optional[str]]:
            if not str(index).isnumeric() or int(index) > len(gist_strings):
                return False, ctx.fmt('index_error', len(gist_strings))
            return True, None

        if ind:
            if (i := validate_index(ind))[0]:
                await base_msg.delete()
                await ctx.send(embed=await self.build_gist_embed(ctx, data, int(ind), ctx.l.gist.content_notice))
                return
            await ctx.send(i[1], delete_after=7)

        while True:
            try:
                msg: discord.Message = await self.bot.wait_for('message',
                                                               check=lambda m: (m.channel.id == ctx.channel.id
                                                                                and m.author.id == ctx.author.id),

                                                               timeout=30)
                success, err_msg = validate_index(msg.content)
                if not success:
                    await ctx.error(err_msg, delete_after=7)
                    continue
                break
            except asyncio.TimeoutError:
                timeout_embed = discord.Embed(
                    color=0xffd500,
                    title=ctx.l.gist.timeout.title
                )
                timeout_embed.set_footer(text=ctx.l.gist.timeout.tip)
                await base_msg.edit(embed=timeout_embed)
                return
        await ctx.send(embed=await self.build_gist_embed(ctx, data, int(msg.content), ctx.l.gist.content_notice))

    async def build_gist_embed(self,
                               ctx: GitBotContext,
                               data: dict,
                               index: int,
                               footer: Optional[str] = None) -> discord.Embed:
        ctx.fmt.set_prefix('gist')
        gist: dict = data['gists']['nodes'][index - 1 if index != 0 else 1]
        embed = discord.Embed(
            color=await self.get_color_from_files(gist['files']),
            title=gist['description'],
            url=gist['url']
        )
        first_file: dict = gist['files'][0]

        created_at: str = ctx.fmt('created_at',
                                  Mgr.to_github_hyperlink(data['login']),
                                  Mgr.github_to_discord_timestamp(gist['createdAt'])) + '\n'

        updated_at: str = ctx.fmt('updated_at', Mgr.github_to_discord_timestamp(gist['updatedAt'])) + '\n'

        stargazers = ctx.fmt('stargazers plural', gist['stargazerCount'], f"{gist['url']}/stargazers") if gist[
                                                                                                   'stargazerCount'] != 1 else ctx.fmt('stargazers singular', f"{gist['url']}/stargazers")
        if gist['stargazerCount'] == 0:
            stargazers = ctx.l.gist.stargazers.no_stargazers
        comment_count = gist['comments']['totalCount']
        comments = f' {ctx.l.gist.linking_word} ' + ctx.fmt('comments plural', comment_count, gist['url']) if comment_count != 1 else ctx.fmt('comments singular', gist['url'])
        if gist['stargazerCount'] == 0:
            comments = f' {ctx.l.gist.linking_word} {ctx.l.gist.comments.no_comments}'

        stargazers_and_comments = f'{stargazers} and {comments}'
        info: str = f'{created_at}{updated_at}{stargazers_and_comments}'
        embed.add_field(name=f':notepad_spiral: {ctx.l.gist.glossary[0]}:', value=f"```{self.extension(first_file['extension'])}\n{first_file['text'][:449]}```")
        embed.add_field(name=f":mag_right: {ctx.l.gist.glossary[1]}:", value=info, inline=False)

        if footer:
            embed.set_footer(text=footer)

        return embed

    async def get_color_from_files(self, files: list) -> int:
        extensions: list = [f['extension'] for f in files]
        most_common: Optional[str] = await Mgr.get_most_common(extensions)
        if most_common in ['.md', '']:
            return Mgr.c.rounded
        for file in files:
            if all([file['extension'] == most_common, file['language'], file['language']['color']]):
                return int(file['language']['color'][1:], 16)
        return Mgr.c.rounded

    def extension(self, ext: str) -> str:
        ext: str = ext[1:]
        if ext == 'ts':
            return 'js'
        return ext if ext in DISCORD_MD_LANGS else ''


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Gist(bot))
