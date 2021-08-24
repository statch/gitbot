import discord
import datetime
from typing import Optional, Union
from lib.globs import Git, Mgr
from discord.ext import commands
from lib.utils.decorators import gitbot_group
from lib.typehints import Organization


class Org(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot

    @gitbot_group(name='org', aliases=['o'], invoke_without_command=True)
    async def org_command_group(self, ctx: commands.Context, org: Optional[Organization] = None) -> None:
        if not org:
            stored: Optional[str] = await Mgr.db.users.getitem(ctx, 'org')
            if stored:
                ctx.invoked_with_stored = True
                await ctx.invoke(self.org_info_command, organization=stored)
            else:
                await ctx.err(ctx.l.generic.nonexistent.org.qa)
        else:
            await ctx.invoke(self.org_info_command, organization=org)

    @commands.cooldown(15, 30, commands.BucketType.user)
    @org_command_group.command(name='info', aliases=['i'])
    async def org_info_command(self, ctx: commands.Context, organization: Organization) -> None:
        ctx.fmt.set_prefix('org info')
        if hasattr(ctx, 'data'):
            org: dict = getattr(ctx, 'data')
        else:
            org: dict = await Git.get_org(organization)
        if not org:
            if hasattr(ctx, 'invoked_with_stored'):
                await Mgr.db.users.delitem(ctx, 'org')
                await ctx.err(ctx.l.generic.nonexistent.org.qa_changed)
            else:
                await ctx.err(ctx.l.generic.nonexistent.org.base)
            return None

        embed = discord.Embed(
            color=0xefefef,
            title=ctx.fmt('title', organization) if organization[0].isupper() else ctx.fmt('title',
                                                                                           organization.lower()),
            url=org['html_url']
        )

        mem: list = await Git.get_org_members(organization)
        members: str = ctx.fmt('members', len(mem), f"({org['html_url']}/people)") + '\n'
        if len(mem) == 1:
            members: str = ctx.fmt('one_member', f"({org['html_url']}/people)") + '\n'
        email: str = f"Email: {org['email']}\n" if 'email' in org and org["email"] is not None else '\n'
        if org['description'] is not None and len(org['description']) > 0:
            embed.add_field(name=f":notepad_spiral: {ctx.l.org.info.glossary[0]}:", value=f"```{org['description']}```")
        repos: str = f"{ctx.l.org.info.repos.no_repos}\n" if org['public_repos'] == 0 else ctx.fmt('repos plural',
                                                                                                   org['public_repos'],
                                                                                                   f"{org['url']}?tab=repositories") + '\n'
        if org['public_repos'] == 1:
            repos: str = ctx.fmt('repos singular', f"{org['url']}?tab=repositories") + '\n'
        if 'location' in org and org['location'] is not None:
            location: str = ctx.fmt('location', org['location']) + '\n'
        else:
            location: str = "\n"

        created_at: str = ctx.fmt('created_at',
                                  f'<t:{int(datetime.datetime.strptime(org["created_at"], "%Y-%m-%dT%H:%M:%SZ").timestamp())}>') + '\n'
        info: str = f"{created_at}{repos}{members}{location}{email}"
        embed.add_field(name=f":mag_right: {ctx.l.org.info.glossary[1]}:", value=info, inline=False)
        blog: tuple = (org['blog'] if 'blog' in org else None, ctx.l.org.info.glossary[3])
        twitter: tuple = (
            f'https://twitter.com/{org["twitter_username"]}' if "twitter_username" in org and org[
                'twitter_username'] is not None else None,
            "Twitter")
        links: list = [blog, twitter]
        link_strings: list = []
        for lnk in links:
            if lnk[0] is not None and len(lnk[0]) != 0:
                link_strings.append(f"- [{lnk[1]}]({lnk[0]})")
        if len(link_strings) != 0:
            embed.add_field(name=f":link: {ctx.l.org.info.glossary[2]}:", value='\n'.join(link_strings), inline=False)
        embed.set_thumbnail(url=org['avatar_url'])
        await ctx.send(embed=embed)

    @commands.cooldown(15, 30, commands.BucketType.user)
    @org_command_group.command(name='repos', aliases=['r'])
    async def org_repos_command(self, ctx: commands.Context, org: Organization) -> None:
        ctx.fmt.set_prefix('org repos')
        o: Union[dict, None] = await Git.get_org(org)
        repos: list = [x for x in await Git.get_org_repos(org)]
        if o is None:
            await ctx.err(ctx.l.generic.nonexistent.org.base)
            return
        if not repos:
            await ctx.err(ctx.l.generic.nonexistent.repos.org)
            return
        embed: discord.Embed = discord.Embed(
            title=ctx.fmt('owner', org) if org[0].isupper() else ctx.fmt('owner', org).lower(),
            description='\n'.join(
                [f':white_small_square: [**{x["name"]}**]({x["html_url"]})' for x in repos[:15]]),
            color=0xefefef,
            url=f"https://github.com/{org}"
        )
        if (c := len(repos)) > 15:
            more: str = str(c - 15)
            embed.set_footer(text=ctx.fmt('more', more))
        embed.set_thumbnail(url=o["avatar_url"])
        await ctx.send(embed=embed)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Org(bot))
