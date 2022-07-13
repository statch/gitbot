import io
import discord
import plotly.express as px
import plotly.io
import plotly.graph_objects as go
import pandas as pd
from discord.ext import commands
from lib.utils.decorators import gitbot_group
from typing import Optional
from lib.globs import Crates as CratesAPI, Mgr
from lib.typehints import CratesIOCrate
from lib.structs import GitBotEmbed
from lib.structs.discord.context import GitBotContext


class Crates(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot

    @gitbot_group('crates', invoke_without_command=True, aliases=['crate', 'crates.io'])
    @commands.cooldown(5, 30, commands.BucketType.user)
    async def crates_command_group(self, ctx: GitBotContext, crate: Optional[CratesIOCrate] = None) -> None:
        if crate is not None:
            await ctx.invoke(self.crate_info_command, crate=crate)
        else:
            commands_: list = [
                f'`git crates {{{ctx.l.help.argument_explainers.rust_crate_name.name}}}` - {ctx.l.crates.default.commands.info}',
                f'`git crates downloads {{{ctx.l.help.argument_explainers.rust_crate_name.name}}}` - {ctx.l.crates.default.commands.downloads}'
            ]
            embed: GitBotEmbed = GitBotEmbed(
                color=Mgr.c.languages.rust,
                title=ctx.l.crates.default.title,
                description=ctx.l.crates.default.description
                + '\n\n'
                + '\n'.join(commands_),
                thumbnail=Mgr.i.crates_logo,
                url='https://crates.io/'
            )
            await ctx.send(embed=embed)

    @crates_command_group.command('info', aliases=['i'])
    @commands.cooldown(5, 30, commands.BucketType.user)
    async def crate_info_command(self, ctx: GitBotContext, crate: CratesIOCrate) -> None:
        ctx.fmt.set_prefix('crates info')
        data: Optional[dict] = await CratesAPI.get_crate_data(crate.lower())
        if data:
            owners: list = await CratesAPI.get_crate_owners(crate.lower())
            crate_url: str = f'https://crates.io/crates/{data["crate"]["name"]}'
            embed: GitBotEmbed = GitBotEmbed(
                color=0xe7b34e,
                title=f'{data["crate"]["name"]} `{data["crate"]["newest_version"]}`',
                url=data['crate'].get('homepage', crate_url),
                thumbnail=owners[0]['avatar']
            )

            if (crate_desc := data['crate']['description']) is not None and len(crate_desc) != 0:
                embed.add_field(name=f":notepad_spiral: {ctx.l.crates.info.glossary[0]}:",
                                value=f"```{crate_desc.strip()}```")

            more_authors: str = f' {ctx.fmt("more_authors", f"[{len(owners) - 5}]({crate_url})")}' if len(owners) > 5 else ''
            authors: str = ctx.fmt('authors',
                                   ', '.join(f'[{owner["name"]}{" `(team)`" if owner["kind"] == "team" else ""}]'
                                             f'({owner["url"]})' for owner in owners[:5])) + more_authors + '\n'

            created_at: str = ctx.fmt('created_at',
                                      Mgr.external_to_discord_timestamp(data['crate']['created_at'],
                                                                        '%Y-%m-%dT%H:%M:%S.%f%z')) + '\n'

            all_time_downloads: str = f'```rust\n{data["crate"]["downloads"]} //' \
                                      f' {ctx.l.crates.info.all_time_downloads}```\n'
            info: str = f'{authors}{created_at}{all_time_downloads}'
            embed.add_field(name=f":mag_right: {ctx.l.crates.info.glossary[1]}:", value=info)

            links: list = []
            link_strings: list = []
            for lnk in links:
                if lnk[0] is not None and len(lnk[0]) != 0:
                    link_strings.append(f"- [{lnk[1]}]({lnk[0]})")
            if len(link_strings) != 0:
                embed.add_field(name=f":link: {ctx.l.pypi.info.glossary[2]}:",
                                value='\n'.join(link_strings))

            if rendered_kws := Mgr.render_label_like_list(data['crate']['keywords'],
                                                          url_fmt='https://crates.io/keywords/{0}'):
                embed.add_field(name=f':label: {ctx.l.crates.info.glossary[3]}:', value=rendered_kws)

            if rendered_ctgs := Mgr.render_label_like_list(data['categories'],
                                                           url_fmt='https://crates.io/categories/{0}',
                                                           name_and_url_slug_knames_if_dict=('category', 'slug')):
                embed.add_field(name=f':package: {ctx.l.crates.info.glossary[4]}:', value=rendered_ctgs)

            await embed.send(ctx)
        else:
            await ctx.error(ctx.l.generic.nonexistent.rust_crate)

    @crates_command_group.command('downloads', aliases=['dl'])
    @commands.cooldown(3, 30, commands.BucketType.user)
    @commands.max_concurrency(7)
    async def crate_downloads_command(self, ctx: GitBotContext, project: CratesIOCrate) -> None:
        ctx.fmt.set_prefix('crates downloads')
        data: Optional[list] = await CratesAPI.get_crate_downloads(project)
        if data:
            df: pd.DataFrame = pd.DataFrame({'date': [item['date'] for item in data],
                                             'downloads': [item['downloads'] for item in data]})
            fig: go.Figure = px.line(df,
                                     x='date',
                                     y='downloads',
                                     labels={'date': ctx.l.crates.downloads.glossary[0],
                                             'downloads': ctx.l.crates.downloads.glossary[1]},
                                     template='plotly_dark')
            yesterday_dl: int = data[-1]['downloads']
            last_week_dl: int = sum(item['downloads'] for item in data[-7:])
            last_month_dl: int = sum(item['downloads'] for item in data[-30:])
            embed: GitBotEmbed = GitBotEmbed(
                color=Mgr.c.rounded,
                title=ctx.fmt('title', project, len(data) - 1),
                url=f'https://crates.io/crates/{project.replace(".", "-").lower()}',
                description=f'{ctx.fmt("stats yesterday", yesterday_dl)}\n'
                            f'{ctx.fmt("stats last_week", last_week_dl)}\n'
                            f'{ctx.fmt("stats last_month", last_month_dl)}',
                thumbnail=Mgr.i.crates_logo,
                footer=ctx.l.crates.downloads.footer
            )
            await ctx.reply(embed=embed, file=discord.File(fp=io.BytesIO(plotly.io.to_image(fig,
                                                                                            format='png',
                                                                                            engine='kaleido')),
                                                           filename=f'{project}-downloads-overall.png'),
                            mention_author=False)
        else:
            await ctx.error(ctx.l.generic.nonexistent.rust_crate)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Crates(bot))
