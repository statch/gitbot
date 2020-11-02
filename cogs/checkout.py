import aiohttp
import discord
import discord.ext.commands as commands
from ext.decorators import guild_available
from github import UnknownObjectException
from cfg import globals

Git = globals.Git


async def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


http_ses = aiohttp.ClientSession()
assert http_ses.closed is False, "Client session closed"


class Checkout(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.emoji: str = '<:github:772040411954937876>'
        self.square: str = ":white_small_square:"
        self.f: str = "<:file:762378114135097354>"
        self.fd: str = "<:folder:762378091497914398>"

    @guild_available()
    @commands.group(name='checkout', aliases=['c'])
    async def checkout(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.channel.trigger_typing()
            await ctx.send(
                f"{self.emoji} Looks like you're lost! **Use the command** `git --help` **to get back on track.**")

    @guild_available()
    @checkout.group(name='--user', aliases=['-U', '-u'])
    async def user(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.channel.trigger_typing()
            lines: list = [f"**In this subcommand you have two options available:**",
                           f"{self.square} `-info` **|** Returns info about a user",
                           f"{self.square} `-repos` **|** Returns the user's repos"]
            embed = discord.Embed(
                color=0xefefef,
                title=f'{self.emoji}  User Subcommand',
                description=str("\n".join(lines))
            )
            await ctx.send(embed=embed)

    @guild_available()
    @checkout.group(name='--organization', aliases=['--org', '-O', '-o'])
    async def org(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.channel.trigger_typing()
            lines: list = [f"**In this subcommand you have two options available:**",
                           f"{self.square} `-info` **|** Returns info about an organization",
                           f"{self.square} `-repos` **|** Returns the organization's repos"]
            embed = discord.Embed(
                color=0xefefef,
                title=f'{self.emoji}  Organization Subcommand',
                description=str("\n".join(lines))
            )
            await ctx.send(embed=embed)

    @guild_available()
    @checkout.group(name="--repo", aliases=['--repository', '-R', '-r'])
    async def repo(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.channel.trigger_typing()
            lines: list = [f"**In this subcommand you have two options available:**",
                           f"{self.square} `-info` **|** Returns info about a repository",
                           f"{self.square} `-source` **|** Returns the source code of the repository"]
            embed = discord.Embed(
                color=0xefefef,
                title=f'{self.emoji}  Repository Subcommand',
                description=str("\n".join(lines))
            )
            await ctx.send(embed=embed)

    @commands.cooldown(15, 30, commands.BucketType.user)
    @guild_available()
    @user.command(name='-repos', aliases=['-repositories', '-R', '-r'])
    async def _repos(self, ctx, *, user: str) -> None:
        await ctx.channel.trigger_typing()
        try:
            usr = Git.user.get_user(user)
            repos: list = [x for x in usr.get_repos() if not x.private][:15]
        except UnknownObjectException:
            await ctx.send(f"{self.emoji} This user **doesn't exist!**")
            return
        if len(repos) < 1:
            await ctx.send(f"{self.emoji} This user doesn't have any **public repos!**")
            return
        embed = discord.Embed(
            title=f"{user}'s Repos",
            description='\n'.join(
                [f':white_small_square: [**{x.name}**]({x.html_url})' for x in repos]),
            color=0xefefef,
            url=f"{usr.html_url}?tab=repositories"
        )
        if int(usr.raw_data["public_repos"]) > 15:
            embed.set_footer(text=f"View {int(usr.raw_data['public_repos']) - 15} more on GitHub")
        embed.set_thumbnail(url=usr.avatar_url)
        await ctx.send(embed=embed)

    @commands.cooldown(15, 30, commands.BucketType.user)
    @guild_available()
    @org.command(name='-repos', aliases=['-repositories', '-R', 'r'])
    async def _o_repos(self, ctx, *, org: str) -> None:
        await ctx.channel.trigger_typing()
        try:
            o = Git.user.get_organization(org)
            repos: list = [x for x in o.get_repos() if not x.private][:15]
        except UnknownObjectException:
            await ctx.send(f"{self.emoji} This organization **doesn't exist!**")
            return
        if len(repos) < 1:
            await ctx.send(f"{self.emoji} This organization doesn't have any **public repos!**")
            return
        embed = discord.Embed(
            title=f"{org}'s Repos",
            description='\n'.join(
                [f':white_small_square: [**{x.name}**]({x.html_url})' for x in repos]),
            color=0xefefef,
            url=f"{o.html_url}"
        )
        if int(o.raw_data["public_repos"]) > 15:
            embed.set_footer(text=f"View {int(o.raw_data['public_repos']) - 15} more on GitHub")
        embed.set_thumbnail(url=o.avatar_url)
        await ctx.send(embed=embed)

    @commands.cooldown(15, 30, commands.BucketType.user)
    @guild_available()
    @repo.command(name='-src', aliases=['-S', '-source', '-s', '-Src', '-sRc', '-srC', '-SrC'])
    async def files_command(self, ctx, *, repository: str) -> None:
        await ctx.channel.trigger_typing()
        try:
            r = Git.user.get_repo(str(repository))
        except UnknownObjectException:
            await ctx.send(f"{self.emoji} This repository **doesn't exist!**")
            return
        if r.private:
            await ctx.send(f"{self.emoji} This repository **doesn't exist!**")
            return
        src_ = await http_ses.get(r.contents_url[:-7])
        src: list = await src_.json()
        files: list = [f"{self.f}  [{f['name']}]({f['html_url']})" if f['type'] == 'file' else f"{self.fd}  [{f['name']}]({f['html_url']})" for f in src]
        embed = discord.Embed(
            color=0xefefef,
            title=f"{repository}",
            description='\n'.join(files[:15]),
            url=r.html_url
        )
        if int(len(files)) > 15:
            embed.set_footer(text=f"View {len(files) - 15} more on GitHub")
        await ctx.send(embed=embed)

    @repo.command(name="-I", aliases=['-info'])
    @commands.cooldown(15, 30, commands.BucketType.user)
    @guild_available()
    async def repo_info_command(self, ctx, *, repository: str) -> None:
        await ctx.channel.trigger_typing()
        try:
            r = Git.user.get_repo(str(repository))
        except UnknownObjectException:
            await ctx.send(f"{self.emoji} This repository **doesn't exist!**")
            return
        if r.private:
            await ctx.send(f"{self.emoji} This repository **doesn't exist!**")
            return
        embed = discord.Embed(
            color=0xefefef,
            title=f"{repository}",
            description=None,
            url=r.html_url
        )
        brnch: int = r.get_branches().totalCount
        ctr: int = r.get_contributors().totalCount
        if r.description is not None and len(r.description) != 0:
            embed.add_field(name=":notepad_spiral: Description:", value=f"```{r.description}```")
        branches: str = f"Contains [{brnch} branches]({r.html_url}/branches) in total\n" if brnch != 1 else f"Contains only [one branch]({r.html_url}/branches)\n"
        issues: str = f'Doesn\'t have any [open issues]({r.html_url}/issues)\n' if r.open_issues_count == 0 else f"Has [{r.open_issues_count} open issues]({r.html_url}/issues)\n"
        contributors: str = "No one contributed to this repo, yet" if ctr == 0 else f"[{ctr} people]({r.html_url}/contributors) contributed so far"
        if ctr == 1:
            contributors: str = f"[One person]({r.html_url}/contributors) contributed so far"
        if r.open_issues_count == 1:
            issues: str = f"Has only one [open issue]({r.html_url}/issues)"
        forks: str = f"No one has forked this repo, yet\n" if r.forks_count == 0 else f"Has been forked [{r.forks_count} times]({r.html_url}/network/members)\n"
        if r.forks_count == 1:
            forks: str = f"It's been forked [only once]({r.html_url}/network/members)\n"
        info: str = f"Created on {r.created_at.strftime('%e, %b %Y')}\n{branches}{issues}{forks}{contributors}"
        embed.add_field(name=":mag_right: Info:", value=info, inline=False)
        homepage: tuple = (
            r.raw_data['homepage'] if 'homepage' in r.raw_data and r.raw_data['homepage'] is not None else None,
            "Homepage")
        links: list = [homepage]
        link_strings: list = []
        for lnk in links:
            if lnk[0] is not None and len(lnk[0]) != 0:
                link_strings.append(f"- [{lnk[1]}]({lnk[0]})")
        if len(link_strings) != 0:
            embed.add_field(name=f":link: Links:", value='\n'.join(link_strings), inline=False)
        if 'license' in dict(r.raw_data) and r.raw_data['license'] is not None:
            embed.set_footer(text=f'Licensed under the {r.raw_data["license"]["name"]}')
        await ctx.send(embed=embed)

    @commands.cooldown(15, 30, commands.BucketType.user)
    @guild_available()
    @user.command(name='-info', aliases=['-I'])
    async def profile_command(self, ctx, *, user) -> None:
        await ctx.channel.trigger_typing()
        try:
            u = Git.user.get_user(user)
        except UnknownObjectException:
            await ctx.send(f"{self.emoji} This user **doesn't exist!**")
            return
        form: str = 'Profile' if str(user)[0].isupper() else 'profile'
        embed = discord.Embed(
            color=0xefefef,
            title=f"{user}'s {form}",
            description=None,
            url=u.html_url
        )
        orgs_c: int = u.get_orgs().totalCount
        if u.bio is not None and len(u.bio) > 0:
            embed.add_field(name=":notepad_spiral: Bio:", value=f"```{u.bio}```")
        occupation: str = f'Works at {u.company}\n' if u.company is not None else 'Isn\'t part of a company\n'
        orgs: str = f"Belongs to {orgs_c} organizations\n" if orgs_c != 0 else "Doesn't belong to any organizations\n"
        if orgs_c == 1:
            orgs: str = "Belongs to 1 organization\n"
        followers: str = "Isn\'t followed by anyone" if u.followers == 0 else f"Has [{u.followers} followers]({u.html_url}?tab=followers)"
        if u.followers == 1:
            followers: str = f"Has only [1 follower]({u.html_url}?tab=followers)"
        following: str = "doesn't follow anyone, yet" if u.following == 0 else f"follows [{u.following} users]({u.html_url}?tab=following)"
        if u.following == 1:
            following: str = f"follows only [1 person]({u.html_url}?tab=following)"
        follow: str = followers + ' and ' + following
        repos: str = "Has no repositories, yet\n" if u.public_repos == 0 else f"Has a total of [{u.public_repos} repositories]({u.html_url}?tab=repositories)\n"
        if u.public_repos == 1:
            repos: str = f"Has only [1 repository]({u.html_url}?tab=repositories)\n"
        info: str = f"Joined GitHub on {u.created_at.strftime('%e, %b %Y')}\n{repos}{occupation}{orgs}{follow}"
        embed.add_field(name=":mag_right: Info:", value=info, inline=False)
        blog: tuple = (u.blog, "Website")
        twitter: tuple = (
            f'https://twitter.com/{u.twitter_username}' if u.twitter_username is not None else None, "Twitter")
        links: list = [blog, twitter]
        link_strings: list = []
        for lnk in links:
            if lnk[0] is not None and len(lnk[0]) != 0:
                link_strings.append(f"- [{lnk[1]}]({lnk[0]})")
        if len(link_strings) != 0:
            embed.add_field(name=f":link: Links:", value='\n'.join(link_strings), inline=False)
        embed.set_thumbnail(url=u.avatar_url)
        await ctx.send(embed=embed)

    @commands.cooldown(15, 30, commands.BucketType.user)
    @guild_available()
    @org.command(name='-info', aliases=['-I'])
    async def o_profile_command(self, ctx, *, organization) -> None:
        await ctx.channel.trigger_typing()
        try:
            org = Git.user.get_organization(organization)
        except UnknownObjectException:
            await ctx.send(f"{self.emoji} This organization **doesn't exist!**")
            return
        form: str = "Profile" if str(organization)[0].isupper() else 'profile'
        raw: dict = org.raw_data
        embed = discord.Embed(
            color=0xefefef,
            title=f"{organization}'s {form}",
            description=None,
            url=org.html_url
        )
        members: str = f"Has {org.get_members().totalCount} members\n"
        email: str = f"Email: {raw['email']}\n" if 'email' in raw and raw["email"] is not None else '\n'
        if org.description is not None and len(org.description) > 0:
            embed.add_field(name=":notepad_spiral: Description:", value=f"```{org.description}```")
        repos: str = "Has no repositories, yet\n" if org.public_repos == 0 else f"Has a total of [{org.public_repos} repositories]({org.html_url})\n"
        if org.public_repos == 1:
            repos: str = f"Has only [1 repository]({org.html_url})\n"
        if org.location is not None:
            location: str = f"Is based in {org.location}\n"
        else:
            location: str = "\n"
        info: str = f"Created on {org.created_at.strftime('%e, %b %Y')}\n{repos}{members}{location}{email}"
        embed.add_field(name=":mag_right: Info:", value=info, inline=False)
        blog: tuple = (org.blog, "Website")
        twitter: tuple = (
            f'https://twitter.com/{raw["twitter_username"]}' if "twitter_username" in raw and raw[
                'twitter_username'] is not None else None,
            "Twitter")
        links: list = [blog, twitter]
        link_strings: list = []
        for lnk in links:
            if lnk[0] is not None and len(lnk[0]) != 0:
                link_strings.append(f"- [{lnk[1]}]({lnk[0]})")
        if len(link_strings) != 0:
            embed.add_field(name=f":link: Links:", value='\n'.join(link_strings), inline=False)
        embed.set_thumbnail(url=org.avatar_url)
        await ctx.send(embed=embed)


def setup(client):
    client.add_cog(Checkout(client))
