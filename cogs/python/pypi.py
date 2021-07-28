import discord
from discord.ext import commands
from lib.utils.decorators import gitbot_group
from typing import Optional
from lib.globs import PyPI as _PyPI, Mgr
from pkg_resources import parse_version
from datetime import datetime


class PyPI(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot

    @gitbot_group('pypi', invoke_without_command=True)
    @commands.cooldown(5, 30, commands.BucketType.user)
    async def pypi_command_group(self, ctx: commands.Context, project: Optional[str] = None) -> None:
        if project is not None:
            await ctx.invoke(self.project_info_command, project=project)

    @pypi_command_group.command('info')
    @commands.cooldown(5, 30, commands.BucketType.user)
    async def project_info_command(self, ctx: commands.Context, project: str) -> None:
        ctx.fmt.set_prefix('pypi info')
        data: Optional[dict] = await _PyPI.get_project_data(project.lower())
        if data:
            embed: discord.Embed = discord.Embed(
                color=0x3572a5,
                title=f'{data["info"]["name"]} `{data["info"]["version"]}`',
                url=data['info']['project_url']
            )

            gravatar: str = Mgr.construct_gravatar_url(data['info']['author_email'],
                                                       default='https://raw.githubusercontent.com/github/explore/666de02829613e0244e9441b114edb85781e972c/topics/pip/pip.png')
            embed.set_thumbnail(url=gravatar)
            if data['info']['summary'] is not None and len(data['info']['summary']) != 0:
                embed.add_field(name=f":notepad_spiral: {ctx.l.pypi.info.glossary[0]}:",
                                value=f"```{data['info']['summary'].strip()}```")
            author: str = ctx.fmt('author', f'[{(author := data["info"]["author"])}]'
                                            f'({await Mgr.ensure_http_status(f"https://pypi.org/user/{author}", alt="")})') + '\n'

            first_release = (None, None)
            for tag_name, release in data['releases'].items():
                if (v := parse_version(tag_name)) and first_release[0] is None or first_release[0] > v:
                    first_release = v, release
            first_uploaded_at: str = f''
            if first_release[1] is not None:
                first_uploaded_at: str = ctx.fmt('first_upload', f'<t:{int(datetime.strptime(first_release[1][0]["upload_time"], "%Y-%m-%dT%H:%M:%S").timestamp())}>') + '\n'

            requires_python: str = ctx.fmt('requires_python', f'`{data["info"]["requires_python"]}`') + '\n'
            info: str = f'{author}{first_uploaded_at}{requires_python}'
            embed.add_field(name=f":mag_right: {ctx.l.pypi.info.glossary[1]}:", value=info, inline=False)

            homepage: tuple = (data['info']['home_page'] if 'home_page' in data['info'] and data['info']['home_page'] else None, ctx.l.pypi.info.glossary[3])
            docs: tuple = (data['info']['docs_url'] if 'docs_url' in data['info'] and data['info']['docs_url'] else None, ctx.l.pypi.info.glossary[4])
            bugs: tuple = (data['info']['bugtrack_url'] if 'bugtrack_url' in data['info'] and data['info']['bugtrack_url'] else None, ctx.l.pypi.info.glossary[4])
            links: list = [homepage, docs, bugs]
            link_strings: list = []
            for lnk in links:
                if lnk[0] is not None and len(lnk[0]) != 0:
                    link_strings.append(f"- [{lnk[1]}]({lnk[0]})")
            if len(link_strings) != 0:
                embed.add_field(name=f":link: {ctx.l.pypi.info.glossary[2]}:",
                                value='\n'.join(link_strings),
                                inline=False)

            if 'license' in data['info'] and data['info']['license']:
                embed.set_footer(text=ctx.fmt('license', data['info']['license']))

            await ctx.send(embed=embed)
        else:
            await ctx.err(ctx.l.generic.nonexistent.python_package)

    @pypi_command_group.command('releases')
    @commands.cooldown(5, 30, commands.BucketType.user)
    async def project_releases_command(self, ctx: commands.Context, project: str) -> None:
        pass


def setup(bot: commands.Bot) -> None:
    bot.add_cog(PyPI(bot))
