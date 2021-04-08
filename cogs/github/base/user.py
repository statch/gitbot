import discord
import datetime
from discord.ext import commands
from typing import Union, Optional
from core.globs import Git, Mgr


class User(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot

    @commands.group(name='user', aliases=['u'], invoke_without_command=True)
    async def user_command_group(self, ctx: commands.Context, user: Optional[str] = None) -> None:
        info_command: commands.Command = self.bot.get_command(f'user --info')
        if not user:
            stored = await Mgr.db.users.getitem(ctx, 'user')
            if stored:
                ctx.invoked_with_stored = True
                await ctx.invoke(info_command, user=stored)
            else:
                await Mgr.error(ctx, ctx.l.generic.nonexistent.user.qa)
        else:
            await ctx.invoke(info_command, user=user)

    @commands.cooldown(15, 30, commands.BucketType.user)
    @user_command_group.command(name='--info', aliases=['-i', '-info', 'info'])
    async def user_info_command(self, ctx: commands.Context, user: str) -> None:
        ctx.fmt.set_prefix('user info')
        if hasattr(ctx, 'data'):
            u: dict = getattr(ctx, 'data')
        else:
            u = await Git.get_user(user)
        if not u:
            if hasattr(ctx, 'invoked_with_stored'):
                await Mgr.db.users.delitem(ctx, 'user')
                await Mgr.error(ctx, ctx.l.generic.nonexistent.user.qa_changed)
            else:
                await ctx.send(f"{Mgr.e.err} This user **doesn't exist!**")
            return None

        form: str = 'Profile' if str(user)[0].isupper() else 'profile'
        embed = discord.Embed(
            color=0xefefef,
            title=f"{user}'s {form}",
            url=u['url']
        )

        contrib_count: Union[tuple, None] = u['contributions']
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

        repos: str = "Has no repositories, yet\n" if u[
                                                         'public_repos'] == 0 else f"Has a total of [{u['public_repos']} repositories]({u['url']}?tab=repositories)\n"
        if u['public_repos'] == 1:
            repos: str = f"Has only [1 repository]({u['url']}?tab=repositories)\n"
        if contrib_count is not None:
            contrib: str = f"\n{contrib_count[0]} contributions this year, {contrib_count[1]} today\n"
        else:
            contrib: str = ""

        joined_at: str = ctx.fmt('joined_at', datetime.datetime.strptime(u['createdAt'], '%Y-%m-%dT%H:%M:%SZ').strftime('%e, %b %Y')) + '\n'
        info: str = f"{joined_at}{repos}{occupation}{orgs}{follow}{contrib}"
        embed.add_field(name=f":mag_right: {ctx.l.user.info.glossary[1]}:", value=info, inline=False)
        w_url: str = u['websiteUrl']
        if w_url:
            blog: tuple = (w_url if w_url.startswith(('https://', 'http://')) else f'http://{w_url}', "Website")
        else:
            blog: tuple = (None, 'Website')
        twitter: tuple = (
            f'https://twitter.com/{u["twitterUsername"]}' if "twitterUsername" in u else None, "Twitter")
        links: list = [blog, twitter]
        link_strings: list = []
        for lnk in links:
            if lnk[0] is not None and len(lnk[0]) != 0:
                link_strings.append(f"- [{lnk[1]}]({lnk[0]})")
        if len(link_strings) != 0:
            embed.add_field(name=f":link: {ctx.l.user.info.glossary[2]}:", value='\n'.join(link_strings), inline=False)
        embed.set_thumbnail(url=u['avatarUrl'])
        await ctx.send(embed=embed)

    @commands.cooldown(15, 30, commands.BucketType.user)
    @user_command_group.command(name='--repos', aliases=['-r', '-repos', 'repos'])
    async def user_repos_command(self, ctx: commands.Context, user: str) -> None:
        ctx.fmt.set_prefix('user repos')
        u: Union[dict, None] = await Git.get_user(user)
        repos = await Git.get_user_repos(user)
        if u is None:
            await Mgr.error(ctx, ctx.l.generic.nonexistent.user.base)
            return
        if not repos:
            await Mgr.error(ctx, ctx.l.user.repos.no_public)
            return
        form: str = 'Repos' if user[0].isupper() else 'repos'
        embed: discord.Embed = discord.Embed(
            title=f"{user}'s {form}",
            description='\n'.join(
                [f':white_small_square: [**{x["name"]}**]({x["html_url"]})' for x in repos[:15]]),
            color=0xefefef,
            url=f"https://github.com/{user}"
        )
        if (c := len(repos)) > 15:
            more: str = str(c - 15)
            embed.set_footer(text=ctx.fmt('more', more))
        embed.set_thumbnail(url=u["avatarUrl"])
        await ctx.send(embed=embed)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(User(bot))
