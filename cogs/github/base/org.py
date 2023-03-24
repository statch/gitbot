import discord
from typing import Optional
from discord.ext import commands
from lib.utils.decorators import gitbot_group
from lib.typehints import GitHubOrganization
from lib.structs.discord.context import GitBotContext
from lib.structs import GitBot


class Org(commands.Cog):
    def __init__(self, bot: GitBot):
        self.bot: GitBot = bot

    @gitbot_group(name='org', aliases=['o'], invoke_without_command=True)
    async def org_command_group(self, ctx: GitBotContext, org: Optional[GitHubOrganization] = None) -> None:
        if not org:
            stored: Optional[str] = await self.bot.mgr.db.users.getitem(ctx, 'org')
            if stored:
                ctx.invoked_with_stored = True
                await ctx.invoke(self.org_info_command, organization=stored)
            else:
                await ctx.error(ctx.l.generic.nonexistent.org.qa)
        else:
            await ctx.invoke(self.org_info_command, organization=org)

    @commands.cooldown(15, 30, commands.BucketType.user)
    @org_command_group.command(name='info', aliases=['i'])
    async def org_info_command(self, ctx: GitBotContext, organization: Optional[GitHubOrganization]) -> None:
        if not organization:
            return await ctx.invoke(self.org_command_group)
        ctx.fmt.set_prefix('org info')
        if ctx.data:
            org: dict = getattr(ctx, 'data')
        else:
            org: dict = await self.bot.github.get_org(organization)
        if not org:
            if ctx.invoked_with_stored:
                await self.bot.mgr.db.users.delitem(ctx, 'org')
                await ctx.error(ctx.l.generic.nonexistent.org.qa_changed)
            else:
                await ctx.error(ctx.l.generic.nonexistent.org.base)
            return None

        embed = discord.Embed(
            color=self.bot.mgr.c.rounded,
            title=ctx.fmt('title', organization) if organization[0].isupper() else ctx.fmt('title',
                                                                                           organization.lower()),
            url=org['html_url']
        )

        mem: list = await self.bot.github.get_org_members(organization)
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

        created_at: str = ctx.fmt('created_at', self.bot.mgr.github_to_discord_timestamp(org['created_at'])) + '\n'
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
        await ctx.send(embed=embed, view_on_url=org['html_url'])

    @commands.cooldown(15, 30, commands.BucketType.user)
    @org_command_group.command(name='repos', aliases=['r'])
    async def org_repos_command(self, ctx: GitBotContext, org: GitHubOrganization) -> None:
        ctx.fmt.set_prefix('org repos')
        o: Optional[dict] = await self.bot.github.get_org(org)
        repos: list = await self.bot.github.get_org_repos(org)
        if o is None:
            await ctx.error(ctx.l.generic.nonexistent.org.base)
            return
        if not repos:
            await ctx.error(ctx.l.generic.nonexistent.repos.org)
            return
        embed: discord.Embed = discord.Embed(
            title=ctx.fmt('owner', org) if org[0].isupper() else ctx.fmt('owner', org).lower(),
            description='\n'.join(
                [f':white_small_square: [**{x["name"]}**]({x["html_url"]})' for x in repos[:15]]),
            color=self.bot.mgr.c.rounded,
            url=f'https://github.com/orgs/{org}/repositories'
        )
        if (c := len(repos)) > 15:
            more: str = str(c - 15)
            embed.set_footer(text=ctx.fmt('more', more))
        embed.set_thumbnail(url=o["avatar_url"])
        await ctx.send(embed=embed, view_on_url=f'https://github.com/orgs/{org}/repositories')


async def setup(bot: GitBot) -> None:
    await bot.add_cog(Org(bot))
