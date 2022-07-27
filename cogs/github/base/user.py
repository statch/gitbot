import discord
from discord.ext import commands
from typing import Optional
from lib.globs import Git, Mgr
from lib.utils.decorators import gitbot_group
from lib.typehints import GitHubUser
from lib.structs.discord.context import GitBotContext


class User(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot

    @gitbot_group(name='user', aliases=['u'], invoke_without_command=True)
    async def user_command_group(self, ctx: GitBotContext, user: Optional[str] = None) -> None:
        if not user:
            stored: Optional[str] = await Mgr.db.users.getitem(ctx, 'user')
            if stored:
                ctx.invoked_with_stored = True
                await ctx.invoke(self.user_info_command, user=stored)
            else:
                await ctx.error(ctx.l.generic.nonexistent.user.qa)
        else:
            await ctx.invoke(self.user_info_command, user=user)

    @commands.cooldown(15, 30, commands.BucketType.user)
    @user_command_group.command(name='info', aliases=['i'])
    async def user_info_command(self, ctx: GitBotContext, user: Optional[GitHubUser] = None) -> None:
        if not user:
            return await ctx.invoke(self.user_command_group)
        ctx.fmt.set_prefix('user info')
        if ctx.data:
            u: dict = getattr(ctx, 'data')
        else:
            u: dict = await Git.get_user(user)
        if not u:
            if ctx.invoked_with_stored:
                await Mgr.db.users.delitem(ctx, 'user')
                await ctx.error(ctx.l.generic.nonexistent.user.qa_changed)
            else:
                await ctx.error(ctx.l.generic.nonexistent.user.base)
            return None

        embed = discord.Embed(
            color=Mgr.c.rounded,
            title=ctx.fmt('title', user) if user[0].isupper() else ctx.fmt('title', user.lower()),
            url=u['url']
        )

        contrib_count: Optional[tuple] = u['contributions']
        orgs_c: int = u['organizations']
        if "bio" in u and u['bio'] is not None and len(u['bio']) > 0:
            embed.add_field(name=f":notepad_spiral: {ctx.l.user.info.glossary[0]}:", value=f"```{u['bio']}```")
        occupation: str = (ctx.l.user.info.company + '\n').format(u['company']) if "company" in u and u[
            "company"] is not None else ctx.l.user.info.no_company + '\n'
        orgs: str = ctx.l.user.info.orgs.plural.format(orgs_c) + '\n' if orgs_c != 0 else ctx.l.user.info.orgs.no_orgs
        if orgs_c == 1:
            orgs: str = f"{ctx.l.user.info.orgs.singular}\n"
        followers: str = ctx.l.user.info.followers.no_followers if u[
                                                            'followers'] == 0 else ctx.fmt('followers plural', u['followers'], u['url'] + '?tab=followers')

        if u['followers'] == 1:
            followers: str = ctx.fmt('followers singular', u['url'] + '?tab=followers')
        following: str = ctx.l.user.info.following.no_following if u[
                                                             'following'] == 0 else ctx.fmt('following plural', u['following'], u['url'] + '?tab=following')
        if u['following'] == 1:
            following: str = ctx.fmt('following singular', f'{u["url"]}?tab=following')
        follow: str = followers + f' {ctx.l.user.info.linking_word} ' + following

        repos: str = f"{ctx.l.user.info.repos.no_repos}\n" if u[
                                                         'public_repos'] == 0 else ctx.fmt('repos plural', u['public_repos'], f"{u['url']}?tab=repositories") + '\n'
        if u['public_repos'] == 1:
            repos: str = ctx.fmt('repos singular', f"{u['url']}?tab=repositories") + '\n'
        if contrib_count is not None:
            contrib: str = '\n' + ctx.fmt('contributions', contrib_count[0], contrib_count[1]) + '\n'
        else:
            contrib: str = ""

        joined_at: str = ctx.fmt('joined_at', Mgr.github_to_discord_timestamp(u['createdAt'])) + '\n'

        info: str = f"{joined_at}{repos}{occupation}{orgs}{follow}{contrib}"
        embed.add_field(name=f":mag_right: {ctx.l.user.info.glossary[1]}:", value=info, inline=False)
        w_url: str = u['websiteUrl']
        if w_url:
            blog: tuple = (w_url if w_url.startswith(('https://', 'http://')) else f'https://{w_url}', ctx.l.user.info.glossary[3])
        else:
            blog: tuple = (None, ctx.l.glossary.website.capitalize())
        twitter: tuple = ((
            f'https://twitter.com/{u["twitterUsername"]}') if "twitterUsername" in u and u['twitterUsername'] is not None else None, "Twitter")
        links: list = [blog, twitter]
        link_strings: list = []
        for lnk in links:
            if lnk[0] is not None and lnk[0] != '':
                link_strings.append(f"- [{lnk[1]}]({lnk[0]})")
        if len(link_strings) != 0:
            embed.add_field(name=f":link: {ctx.l.user.info.glossary[2]}:", value='\n'.join(link_strings), inline=False)
        embed.set_thumbnail(url=u['avatarUrl'])
        await ctx.send(embed=embed)

    @commands.cooldown(15, 30, commands.BucketType.user)
    @user_command_group.command(name='repos', aliases=['r'])
    async def user_repos_command(self, ctx: GitBotContext, user: GitHubUser) -> None:
        ctx.fmt.set_prefix('user repos')
        u: Optional[dict] = await Git.get_user(user)
        repos = await Git.get_user_repos(user)
        if u is None:
            await ctx.error(ctx.l.generic.nonexistent.user.base)
            return
        if not repos:
            await ctx.error(ctx.l.user.repos.no_public)
            return
        title: str = ctx.fmt('owner', user) if user[0].isupper() else ctx.fmt('owner', user).lower()
        embed: discord.Embed = discord.Embed(
            title=title,
            description='\n'.join(
                [f':white_small_square: [**{x["name"]}**]({x["html_url"]})' for x in repos[:15]]),
            color=Mgr.c.rounded,
            url=f"https://github.com/{user}"
        )
        if (c := len(repos)) > 15:
            more: str = str(c - 15)
            embed.set_footer(text=ctx.fmt('more', more))
        embed.set_thumbnail(url=u["avatarUrl"])
        await ctx.send(embed=embed)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(User(bot))
