import datetime
from typing import Optional, Union

import discord
from discord.ext import commands

from core.globs import Git


class User(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot
        self.emoji: str = "<:github:772040411954937876>"
        self.e: str = "<:ge:767823523573923890>"

    @commands.group(name="user", aliases=["u"], invoke_without_command=True)
    async def user_command_group(
        self, ctx: commands.Context, user: Optional[str] = None
    ) -> None:
        info_command: commands.Command = self.bot.get_command(f"user --info")
        if not user:
            stored = await self.bot.get_cog("Config").getitem(ctx, "user")
            if stored:
                ctx.invoked_with_stored = True
                await ctx.invoke(info_command, user=stored)
            else:
                await ctx.send(
                    f"{self.e}  You don't have a quick access user configured! **Type** `git config` **to do it.**"
                )
        else:
            await ctx.invoke(info_command, user=user)

    @commands.cooldown(15, 30, commands.BucketType.user)
    @user_command_group.command(name="--info", aliases=["-i", "-info"])
    # TODO Rework this a little
    async def user_info_command(self, ctx: commands.Context, user: str) -> None:
        if hasattr(ctx, "data"):
            u: dict = getattr(ctx, "data")
        else:
            u = await Git.get_user(user)
        if not u:
            if hasattr(ctx, "invoked_with_stored"):
                await self.bot.get_cog("Store").delete_user_field(ctx=ctx)
                await ctx.send(
                    f"{self.e}  The user you had saved has changed their name or deleted their account. Please "
                    f"**re-add them** using `git --config -user`"
                )
            else:
                await ctx.send(f"{self.emoji} This user **doesn't exist!**")
            return None

        form: str = "Profile" if str(user)[0].isupper() else "profile"
        embed = discord.Embed(
            color=0xEFEFEF, title=f"{user}'s {form}", description=None, url=u["url"]
        )

        contrib_count: Union[tuple, None] = u["contributions"]
        orgs_c: int = u["organizations"]
        if "bio" in u and u["bio"] is not None and len(u["bio"]) > 0:
            embed.add_field(name=":notepad_spiral: Bio:", value=f"```{u['bio']}```")
        occupation: str = (
            f'Works at {u["company"]}\n'
            if "company" in u and u["company"] is not None
            else "Isn't part of a company\n"
        )
        orgs: str = (
            f"Belongs to {orgs_c} organizations\n"
            if orgs_c != 0
            else "Doesn't belong to any organizations\n"
        )
        if orgs_c == 1:
            orgs: str = "Belongs to 1 organization\n"
        followers: str = (
            "Isn't followed by anyone"
            if u["followers"] == 0
            else f"Has [{u['followers']} followers]({u['url']}?tab=followers)"
        )

        if u["followers"] == 1:
            followers: str = f"Has only [1 follower]({u['url']}?tab=followers)"
        following: str = (
            "doesn't follow anyone, yet"
            if u["following"] == 0
            else f"follows [{u['following']} users]({u['url']}?tab=following)"
        )
        if u["following"] == 1:
            following: str = f"follows only [1 person]({u['url']}?tab=following)"
        follow: str = followers + " and " + following

        repos: str = (
            "Has no repositories, yet\n"
            if u["public_repos"] == 0
            else f"Has a total of [{u['public_repos']} repositories]({u['url']}?tab=repositories)\n"
        )
        if u["public_repos"] == 1:
            repos: str = f"Has only [1 repository]({u['url']}?tab=repositories)\n"
        if contrib_count is not None:
            contrib: str = f"\n{contrib_count[0]} contributions this year, {contrib_count[1]} today\n"
        else:
            contrib: str = ""

        joined_at = f"Joined GitHub on {datetime.datetime.strptime(u['createdAt'], '%Y-%m-%dT%H:%M:%SZ').strftime('%e, %b %Y')}\n"
        info: str = f"{joined_at}{repos}{occupation}{orgs}{follow}{contrib}"
        embed.add_field(name=":mag_right: Info:", value=info, inline=False)
        blog: tuple = (u["websiteUrl"], "Website")
        twitter: tuple = (
            f'https://twitter.com/{u["twitterUsername"]}'
            if "twitterUsername" in u
            else None,
            "Twitter",
        )
        links: list = [blog, twitter]
        link_strings: list = []
        for lnk in links:
            if lnk[0] is not None and len(lnk[0]) != 0:
                link_strings.append(f"- [{lnk[1]}]({lnk[0]})")
        if len(link_strings) != 0:
            embed.add_field(
                name=f":link: Links:", value="\n".join(link_strings), inline=False
            )
        embed.set_thumbnail(url=u["avatarUrl"])
        await ctx.send(embed=embed)

    @commands.cooldown(15, 30, commands.BucketType.user)
    @user_command_group.command(name="--repos", aliases=["-r", "-repos"])
    async def user_repos_command(self, ctx: commands.Context, user: str) -> None:
        u: Union[dict, None] = await Git.get_user(user)
        repos = await Git.get_user_repos(user)
        if u is None:
            await ctx.send(f"{self.emoji} This repo **doesn't exist!**")
            return
        if not repos:
            await ctx.send(f"{self.emoji} This user doesn't have any **public repos!**")
            return
        form: str = "Repos" if user[0].isupper() else "repos"
        embed: discord.Embed = discord.Embed(
            title=f"{user}'s {form}",
            description="\n".join(
                [
                    f':white_small_square: [**{x["name"]}**]({x["html_url"]})'
                    for x in repos[:15]
                ]
            ),
            color=0xEFEFEF,
            url=f"https://github.com/{user}",
        )
        if c := len(repos) > 15:
            how_much: str = str(c - 15) if c - 15 < 15 else "15+"
            embed.set_footer(text=f"View {how_much} more on GitHub")
        embed.set_thumbnail(url=u["avatarUrl"])
        await ctx.send(embed=embed)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(User(bot))
