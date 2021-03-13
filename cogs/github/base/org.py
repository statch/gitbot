import datetime
from typing import Optional
from typing import Union

import discord
from discord.ext import commands

from core.globs import Git


class Org(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot
        self.emoji: str = "<:github:772040411954937876>"
        self.e: str = "<:ge:767823523573923890>"

    @commands.group(name="org", aliases=["o"], invoke_without_command=True)
    async def org_command_group(
        self, ctx: commands.Context, org: Optional[str] = None
    ) -> None:
        info_command: commands.Command = self.bot.get_command(f"org --info")
        if not org:
            stored = await self.bot.get_cog("Config").getitem(ctx, "org")
            if stored:
                ctx.invoked_with_stored = True
                await ctx.invoke(info_command, organization=stored)
            else:
                await ctx.send(
                    f"{self.e}  You don't have a quick access org configured! **Type** `git config` **to do it.**"
                )
        else:
            await ctx.invoke(info_command, organization=org)

    @commands.cooldown(15, 30, commands.BucketType.user)
    @org_command_group.command(name="--info", aliases=["-i", "-info"])
    # TODO Add more info and make it nicer
    async def org_info_command(self, ctx: commands.Context, organization: str) -> None:
        if hasattr(ctx, "data"):
            org: dict = getattr(ctx, "data")
        else:
            org = await Git.get_org(organization)
        if not org:
            if hasattr(ctx, "invoked_with_stored"):
                await self.bot.get_cog("Store").delete_org_field(ctx=ctx)
                await ctx.send(
                    f"{self.e}  The organization you had saved has changed its name or was deleted. Please **re-add it** using `git --config -org`"
                )
            else:
                await ctx.send(f"{self.emoji} This organization **doesn't exist!**")
            return None

        form: str = "Profile" if str(organization)[0].isupper() else "profile"
        embed = discord.Embed(
            color=0xEFEFEF,
            title=f"{organization}'s {form}",
            description=None,
            url=org["html_url"],
        )

        mem: list = await Git.get_org_members(organization)
        members: str = f"Has [{len(mem)} public members](https://github.com/orgs/{organization}/people)\n"
        if len(mem) == 1:
            members: str = f"Has only [one public member](https://github.com/orgs/{organization}/people)\n"
        email: str = (
            f"Email: {org['email']}\n"
            if "email" in org and org["email"] is not None
            else "\n"
        )
        if org["description"] is not None and len(org["description"]) > 0:
            embed.add_field(
                name=":notepad_spiral: Description:",
                value=f"```{org['description']}```",
            )
        repos: str = (
            "Has no repositories, yet\n"
            if org["public_repos"] == 0
            else f"Has a total of [{org['public_repos']} repositories]({org['html_url']})\n"
        )
        if org["public_repos"] == 1:
            repos: str = f"Has only [1 repository]({org['html_url']})\n"
        if org["location"] is not None:
            location: str = f"Is based in {org['location']}\n"
        else:
            location: str = "\n"

        created_at = f"Created on {datetime.datetime.strptime(org['created_at'], '%Y-%m-%dT%H:%M:%SZ').strftime('%e, %b %Y')}\n"
        info: str = f"{created_at}{repos}{members}{location}{email}"
        embed.add_field(name=":mag_right: Info:", value=info, inline=False)
        blog: tuple = (org["blog"], "Website")
        twitter: tuple = (
            f'https://twitter.com/{org["twitter_username"]}'
            if "twitter_username" in org and org["twitter_username"] is not None
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
        embed.set_thumbnail(url=org["avatar_url"])
        await ctx.send(embed=embed)

    @commands.cooldown(15, 30, commands.BucketType.user)
    @org_command_group.command(name="--repos", aliases=["-r", "-repos"])
    async def org_repos_command(self, ctx: commands.Context, org: str) -> None:
        o: Union[dict, None] = await Git.get_org(org)
        repos: list = [x for x in await Git.get_org_repos(org)]
        form = "Repos" if org[0].isupper() else "repos"
        if o is None:
            await ctx.send(f"{self.emoji} This organization **doesn't exist!**")
            return
        if not repos:
            await ctx.send(
                f"{self.emoji} This organization doesn't have any **public repos!**"
            )
            return
        embed: discord.Embed = discord.Embed(
            title=f"{org}'s {form}",
            description="\n".join(
                [
                    f':white_small_square: [**{x["name"]}**]({x["html_url"]})'
                    for x in repos[:15]
                ]
            ),
            color=0xEFEFEF,
            url=f"https://github.com/{org}",
        )
        if c := len(repos) > 15:
            how_much: str = str(c - 15) if c - 15 < 15 else "15+"
            embed.set_footer(text=f"View {how_much} more on GitHub")
        embed.set_thumbnail(url=o["avatar_url"])
        await ctx.send(embed=embed)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Org(bot))
