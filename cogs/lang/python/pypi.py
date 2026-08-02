import asyncio
import discord
from discord.ext import commands
from lib.utils.decorators import gitbot_group
from typing import Optional
from pkg_resources import parse_version
from lib.typehints import PyPIProject
from lib.structs import GitBotEmbed, GitBot
from lib.structs.discord.context import GitBotContext
from cogs.lang._download_visualization import gen_downloads_chart_inmemory


class PyPI(commands.Cog):
    def __init__(self, bot: GitBot):
        self.bot: GitBot = bot

    @gitbot_group('pypi', invoke_without_command=True)
    @commands.cooldown(5, 30, commands.BucketType.user)
    async def pypi_command_group(self, ctx: GitBotContext, project: Optional[PyPIProject] = None) -> None:
        if project is not None:
            await ctx.invoke(self.project_info_command, project=project)
        else:
            commands_: list = [
                f'`git pypi {{{ctx.l.help.argument_explainers.python_package_name.name}}}` - {ctx.l.pypi.default.commands.info}',
                f'`git pypi downloads {{{ctx.l.help.argument_explainers.python_package_name.name}}}` - {ctx.l.pypi.default.commands.downloads}'
            ]
            embed: GitBotEmbed = GitBotEmbed(
                    color=self.bot.mgr.c.languages.python,
                    title=ctx.l.pypi.default.title,
                    description=ctx.l.pypi.default.description
                                + '\n\n'
                                + '\n'.join(commands_),
                    thumbnail=self.bot.mgr.i.pip_logo,
                    url='https://pypi.org'
            )
            await ctx.send(embed=embed)

    @pypi_command_group.command('info', aliases=['i'])
    @commands.cooldown(5, 30, commands.BucketType.user)
    async def project_info_command(self, ctx: GitBotContext, project: PyPIProject) -> None:
        ctx.fmt.set_prefix('pypi info')
        data: Optional[dict] = await self.bot.pypi.get_project_data(project.lower())
        if not data:
            return await ctx.error(ctx.l.generic.nonexistent.python_package)
        gravatar: str = (self.bot.mgr.construct_gravatar_url(data['info']['author_email'],
                                                            default=self.bot.mgr.i.pip_logo)
                         if data['info']['author_email'] else self.bot.mgr.i.pip_logo)
        embed: GitBotEmbed = GitBotEmbed(
                color=0x3572a5,
                title=f'{data["info"]["name"]} `{data["info"]["version"]}`',
                url=data['info']['project_url'],
                thumbnail=gravatar
        )

        if data['info']['summary'] is not None and len(data['info']['summary']) != 0:
            embed.add_field(name=f":notepad_spiral: {ctx.l.pypi.info.glossary[0]}:",
                            value=f"```{data['info']['summary'].strip()}```")
        author: str = ctx.fmt('author', f'[{(author := data["info"]["author"])}]'
                                        f'({await self.bot.mgr.ensure_http_status(f"https://pypi.org/user/{author}", alt="")})') + '\n'

        first_release = (None, None)
        for tag_name, release in data['releases'].items():
            if (v := parse_version(tag_name)) and first_release[0] is None or first_release[0] > v:
                first_release = v, release
        first_uploaded_at: str = f''
        first_release: tuple[..., list | ...] | list[..., list | ...]
        if first_release[1]:
            first_uploaded_at: str = ctx.fmt('first_upload',
                                             self.bot.mgr.external_to_discord_timestamp(
                                                     first_release[1][0]["upload_time"],
                                                     "%Y-%m-%dT%H:%M:%S")) + '\n'

        requires_python: str = ctx.fmt('requires_python', f'`{data["info"]["requires_python"]}`') + '\n'
        info: str = f'{author}{first_uploaded_at}{requires_python}'
        embed.add_field(name=f":mag_right: {ctx.l.pypi.info.glossary[1]}:", value=info)

        homepage: tuple = (data['info']['home_page'] if 'home_page' in data['info'] and data['info']['home_page'] else None, ctx.l.pypi.info.glossary[3])
        docs: tuple = (data['info']['docs_url'] if 'docs_url' in data['info'] and data['info']['docs_url'] else None, ctx.l.pypi.info.glossary[4])
        bugs: tuple = (data['info']['bugtrack_url'] if 'bugtrack_url' in data['info'] and data['info']['bugtrack_url'] else None, ctx.l.pypi.info.glossary[4])
        links: list = [homepage, docs, bugs]
        link_strings: list = []
        for lnk in links:
            if lnk[0] is not None and len(lnk[0]) != 0:
                link_strings.append(f"- [{lnk[1]}]({lnk[0]})")
        if len(link_strings) != 0:
            embed.add_field(name=f":link: {ctx.l.pypi.info.glossary[2]}:", value='\n'.join(link_strings))

        if 'license' in data['info'] and data['info']['license']:
            embed.set_footer(text=self.bot.mgr.truncate(ctx.fmt('license', data['info']['license']), length=90, full_word=True))

        await ctx.send(embed=embed, view_on_url=data['info']['project_url'])

    @pypi_command_group.command('downloads', aliases=['dl', 'stats', 'statistics'])
    @commands.cooldown(3, 30, commands.BucketType.user)
    @commands.max_concurrency(7)
    async def project_downloads_command(self, ctx: GitBotContext, project: PyPIProject) -> None:
        ctx.fmt.set_prefix('pypi downloads')

        downloads_overall: Optional[dict] = await self.bot.pypi.get_project_overall_downloads(project)
        downloads_recent_raw: Optional[dict] = await self.bot.pypi.get_project_recent_downloads(project)

        if downloads_overall is False or downloads_recent_raw is False:
            return await ctx.info(ctx.l.errors.external_ratelimit)
        if downloads_overall and downloads_overall.get('data') and downloads_recent_raw and downloads_recent_raw.get(
                'data'):
            data: list = downloads_overall['data']
            downloads_recent: dict = downloads_recent_raw['data']

            embed: GitBotEmbed = GitBotEmbed(
                    color=self.bot.mgr.c.rounded,
                    title=ctx.fmt('title', project, len(data) - 1),
                    url=f'https://pypistats.org/packages/{project.replace(".", "-").lower()}',
                    description=f'{ctx.fmt("stats yesterday", format(downloads_recent.get("last_day", 0), ',d'))}\n'
                                f'{ctx.fmt("stats last_week", format(downloads_recent.get("last_week", 0)), ',d')}\n'
                                f'{ctx.fmt("stats last_month", format(downloads_recent.get("last_month", 0), ',d'))}',
                    thumbnail=self.bot.mgr.i.pip_logo,
                    footer=ctx.l.pypi.downloads.footer
            )

            chart_buf = await self.bot.loop.run_in_executor(None, gen_downloads_chart_inmemory, ctx, data)

            await ctx.reply(
                    embed=embed,
                    file=discord.File(fp=chart_buf, filename=f'{project}-downloads-overall.png'),
                    mention_author=False,
                    view_on_url=f'https://pypistats.org/packages/{project.replace(".", "-").lower()}'
            )
        else:
            await ctx.error(ctx.l.generic.nonexistent.python_package)


async def setup(bot: GitBot) -> None:
    await bot.add_cog(PyPI(bot))
