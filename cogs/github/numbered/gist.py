import discord
from discord.ext import commands
from typing import Optional
from lib.utils.decorators import gitbot_command
from lib.typehints import GitHubUser
from lib.structs import GitBotEmbed, GitBot, GitHubInfoSelectView
from lib.structs.discord.context import GitBotContext

DISCORD_MD_LANGS: tuple = ('java', 'js', 'py', 'css', 'cs', 'c',
                           'cpp', 'html', 'php', 'json', 'xml', 'yml',
                           'nim', 'md', 'go', 'kt')


class Gist(commands.Cog):
    def __init__(self, bot: GitBot):
        self.bot: GitBot = bot

    @gitbot_command(name='gist', aliases=['gists'])
    @commands.cooldown(10, 30, commands.BucketType.user)
    async def gist_command(self,
                           ctx: GitBotContext,
                           user: GitHubUser) -> None:
        ctx.fmt.set_prefix('gist')
        data: dict = await self.bot.github.get_user_gists(user)
        if not data:
            await ctx.error(ctx.l.generic.nonexistent.user.base)
            return
        if (gists := len(data['gists']['nodes'])) < 2:
            if gists == 0:
                await ctx.error(ctx.l.generic.nonexistent.gist)
            else:
                await ctx.send(embed=await self.build_gist_embed(ctx, data, data['gists']['nodes'][0],
                                                                 footer=ctx.l.gist.no_list))
            return

        def gist_url(gist: dict) -> str:
            if not gist['description']:
                return gist['url']
            desc = self.bot.mgr.truncate(gist['description'], 70)
            return f'[{desc}]({gist["url"]})'

        gist_strings: list = [f'{self.bot.mgr.e.square}**{ind + 1} |** {gist_url(gist)}' for ind, gist in
                              enumerate(data['gists']['nodes'])]

        embed: GitBotEmbed = GitBotEmbed(
            color=self.bot.mgr.c.rounded,
            title=ctx.fmt('title', user),
            description='\n'.join(gist_strings),
            url=f'https://gist.github.com/{data["login"]}'
        )

        embed.set_footer(text=ctx.fmt('footer', user))

        async def callback(_, gist):
            await ctx.send(embed=await self.build_gist_embed(ctx, data, gist, ctx.l.gist.content_notice),
                           view_on_url=gist['url'])

        await ctx.send(embed=embed,
                       view=GitHubInfoSelectView(ctx, 'gist', ('{0(description)}', ('files [0] name',)),
                                                 ('{0(createdAt)}', self.bot.mgr.github_timestamp_to_international),
                                                 data['gists']['nodes'], callback, value_key='id'))

    async def build_gist_embed(self,
                               ctx: GitBotContext,
                               data: dict,
                               gist: dict,
                               footer: Optional[str] = None) -> discord.Embed:
        ctx.fmt.set_prefix('gist')
        embed = GitBotEmbed(
            color=await self.get_color_from_files(gist['files']),
            title=gist['description'] if gist['description'] else gist['files'][0]['name'],
            url=gist['url']
        )
        first_file: dict = gist['files'][0]

        created_at: str = ctx.fmt('created_at',
                                  self.bot.mgr.to_github_hyperlink(data['login']),
                                  self.bot.mgr.github_to_discord_timestamp(gist['createdAt'])) + '\n'

        updated_at: str = ctx.fmt('updated_at', self.bot.mgr.github_to_discord_timestamp(gist['updatedAt'])) + '\n'

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
        most_common: Optional[str] = await self.bot.mgr.get_most_common(extensions)
        if most_common in ['.md', '']:
            return self.bot.mgr.c.rounded
        return next(
            (
                int(file['language']['color'][1:], 16)
                for file in files
                if all(
                    [
                        file['extension'] == most_common,
                        file['language'],
                        file['language']['color'],
                    ]
                )
            ),
            self.bot.mgr.c.rounded,
        )

    @staticmethod
    def extension(ext: str) -> str:
        ext: str = ext[1:]
        if ext == 'ts':
            return 'js'
        return ext if ext in DISCORD_MD_LANGS else ''


async def setup(bot: GitBot) -> None:
    await bot.add_cog(Gist(bot))
