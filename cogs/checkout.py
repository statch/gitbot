import discord
import discord.ext.commands as commands
import re
from ext.decorators import guild_available
from cfg import globals
from typing import Union
from datetime import datetime

Git = globals.Git
html_comment_regex = re.compile(r'<!--.*-->', re.MULTILINE | re.DOTALL)


def kill_markdown(text: str) -> str:
    md_chars: list = ['*', '>', '`', '~', '\\']
    for char in md_chars:
        text = text.replace(char, '')
    return text


class Checkout(commands.Cog):
    def __init__(self, client):
        self.client: commands.Bot = client
        self.emoji: str = '<:github:772040411954937876>'
        self.square: str = ":white_small_square:"
        self.f: str = "<:file:762378114135097354>"
        self.fd: str = "<:folder:762378091497914398>"
        self.e: str = "<:ge:767823523573923890>"

    @guild_available()
    @commands.group(name='checkout', aliases=['c'])
    async def checkout(self, ctx: commands.Context) -> None:
        if ctx.invoked_subcommand is None:
            await ctx.send(
                f"{self.emoji} Looks like you're lost! **Use the command** `git --help` **to get back on track.**")

    @guild_available()
    @checkout.group(name='--user', aliases=['-U', '-u'])
    async def user(self, ctx: commands.Context) -> None:
        if ctx.invoked_subcommand is None:
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
    async def org(self, ctx: commands.Context) -> None:
        if ctx.invoked_subcommand is None:
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
    async def repo(self, ctx: commands.Context) -> None:
        if ctx.invoked_subcommand is None:
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
    async def _repos(self, ctx: commands.Context, *, user: str) -> None:
        u: Union[dict, None] = await Git.get_user(user)
        repos = await Git.get_user_repos(user)
        if u is None:
            await ctx.send(f"{self.emoji} This repo **doesn't exist!**")
            return
        if not repos:
            await ctx.send(f"{self.emoji} This user doesn't have any **public repos!**")
            return
        form: str = 'Repos' if user[0].isupper() else 'repos'
        embed: discord.Embed = discord.Embed(
            title=f"{user}'s {form}",
            description='\n'.join(
                [f':white_small_square: [**{x["name"]}**]({x["html_url"]})' for x in repos[:15]]),
            color=0xefefef,
            url=f"https://github.com/{user}"
        )
        if int(u["public_repos"]) > 15:
            how_much: str = str(len(repos) - 15) if len(repos) - 15 < 15 else "15+"
            embed.set_footer(text=f"View {how_much} more on GitHub")
        embed.set_thumbnail(url=u["avatar_url"])
        await ctx.send(embed=embed)

    @commands.cooldown(15, 30, commands.BucketType.user)
    @guild_available()
    @org.command(name='-repos', aliases=['-repositories', '-R', 'r'])
    async def _o_repos(self, ctx: commands.Context, *, org: str) -> None:
        o: Union[dict, None] = await Git.get_org(org)
        repos: list = [x for x in await Git.get_org_repos(org)]
        form = 'Repos' if org[0].isupper() else 'repos'
        if o is None:
            await ctx.send(f"{self.emoji} This organization **doesn't exist!**")
            return
        if not repos:
            await ctx.send(f"{self.emoji} This organization doesn't have any **public repos!**")
            return
        embed: discord.Embed = discord.Embed(
            title=f"{org}'s {form}",
            description='\n'.join(
                [f':white_small_square: [**{x["name"]}**]({x["html_url"]})' for x in repos[:15]]),
            color=0xefefef,
            url=f"https://github.com/{org}"
        )
        if int(o["public_repos"]) > 15:
            how_much: str = str(len(repos) - 15) if len(repos) - 15 < 15 else "15+"
            embed.set_footer(text=f"View {how_much} more on GitHub")
        embed.set_thumbnail(url=o["avatar_url"])
        await ctx.send(embed=embed)

    @commands.cooldown(15, 30, commands.BucketType.user)
    @guild_available()
    @repo.command(name='-src', aliases=['-S', '-source', '-s', '-Src', '-sRc', '-srC', '-SrC', '-files'])
    async def files_command(self, ctx: commands.Context, *, repository: str) -> None:
        is_tree: bool = False
        if repository.count('/') > 1:
            repo = "/".join(repository.split("/", 2)[:2])
            file = repository[len(repo):]
            src = await Git.get_tree_file(repo, file)
            is_tree = True
        else:
            src = await Git.get_repo_files(repository)
        if not src:
            if is_tree:
                await ctx.send(f"{self.emoji} This path **doesn't exist!**")
            else:
                await ctx.send(f"{self.emoji} This repository **doesn't exist!**")
            return
        files: list = [f"{self.f}  [{f['name']}]({f['html_url']})" if f[
                                                                          'type'] == 'file' else f"{self.fd}  [{f['name']}]({f['html_url']})"
                       for f in src[:15]]
        if is_tree:
            link: str = str(src[0]['_links']['html'])
            link = link[:link.rindex('/')]
        else:
            link: str = f"https://github.com/{repository}"
        embed = discord.Embed(
            color=0xefefef,
            title=f"{repository}" if len(repository) <= 60 else "/".join(repository.split("/", 2)[:2]),
            description='\n'.join(files),
            url=link
        )
        if int(len(files)) > 15:
            how_much: str = str(len(files) - 15) if len(files) - 15 < 15 else "15+"
            embed.set_footer(text=f"View {how_much} more on GitHub")
        await ctx.send(embed=embed)

    @repo.command(name="-info", aliases=['-I', '-i', '-Info'])
    @commands.cooldown(15, 30, commands.BucketType.user)
    @guild_available()
    async def repo_info_command(self, ctx: commands.Context, *, repository: str) -> None:
        r: Union[dict, None] = await Git.get_repo(str(repository))
        if not r and hasattr(ctx, 'invoked_with_store'):
            await self.client.get_cog('Store').delete_repo_field(ctx=ctx)
            await ctx.send(
                f"{self.e}  The repository you had saved changed its name or was deleted. Please **re-add it** using `git --config -repo`")
            return
        if r is None:
            await ctx.send(f"{self.emoji} This repository **doesn't exist!**")
            return None
        embed = discord.Embed(
            color=0xefefef,
            title=f"{repository}",
            description=None,
            url=r['html_url']
        )
        watch: int = r['watchers_count']
        star: int = r['stargazers_count']
        if r['description'] is not None and len(r['description']) != 0:
            embed.add_field(name=":notepad_spiral: Description:", value=f"```{r['description']}```")
        watchers: str = f"Has [{watch} watchers]({r['html_url']}/watchers) in total\n" if watch != 1 else f"Has only [one watcher]({r['html_url']}/watchers)\n"
        if watch == 0:
            watchers: str = f"Doesn't have any [watchers]({r['html_url']}/watchers)"
        issues: str = f'Doesn\'t have any [open issues]({r["html_url"]}/issues)\n' if r[
                                                                                          'open_issues_count'] == 0 else f"Has [{r['open_issues_count']} open issues]({r['html_url']}/issues)\n"
        stargazers: str = f"No one has [starred]({r['html_url']}/stargazers) to this repo, yet\n" if star == 0 else f"[{star} people]({r['html_url']}/stargazers) starred so far\n"
        if star == 1:
            stargazers: str = f"[One person]({r['html_url']}/stargazers) starred this so far\n"
        if r['open_issues_count'] == 1:
            issues: str = f"Has only one [open issue]({r['html_url']}/issues)\n"
        forks: str = f"No one has forked this repo, yet\n" if r[
                                                                  'forks_count'] == 0 else f"Has been forked [{r['forks_count']} times]({r['html_url']}/network/members)\n"
        if r['forks_count'] == 1:
            forks: str = f"It's been forked [only once]({r['html_url']}/network/members)\n"
        forked = ""
        if 'fork' in r and r['fork'] is True:
            forked = f"This repo is a fork of [{r['parent']['full_name']}]({r['parent']['html_url']})\n"
        info: str = f"Created on {datetime.strptime(r['created_at'], '%Y-%m-%dT%H:%M:%SZ').strftime('%e, %b %Y')}\n{issues}{forks}{watchers}{stargazers}{forked}"
        embed.add_field(name=":mag_right: Info:", value=info, inline=False)
        homepage: tuple = (
            r['homepage'] if 'homepage' in r else None,
            "Homepage")
        links: list = [homepage]
        link_strings: list = []
        for lnk in links:
            if lnk[0] is not None and len(lnk[0]) != 0:
                link_strings.append(f"- [{lnk[1]}]({lnk[0]})")
        if len(link_strings) != 0:
            embed.add_field(name=f":link: Links:", value='\n'.join(link_strings), inline=False)
        if 'license' in r and r['license'] is not None and r['license']["name"].lower() != 'other':
            embed.set_footer(text=f'Licensed under the {r["license"]["name"]}')
        await ctx.send(embed=embed)

    @commands.cooldown(15, 30, commands.BucketType.user)
    @guild_available()
    @user.command(name='-info', aliases=['-I', '-i', '-Info'])
    async def profile_command(self, ctx: commands.Context, *, user: str) -> None:
        u = await Git.get_user(user)
        if not u and hasattr(ctx, 'invoked_with_store'):
            await self.client.get_cog('Store').delete_user_field(ctx=ctx)
            await ctx.send(
                f"{self.e}  The user you had saved has changed their name or deleted their account. Please **re-add them** using `git --config -user`")
            return
        if u is None:
            await ctx.send(f"{self.emoji} This user **doesn't exist!**")
            return None
        form: str = 'Profile' if str(user)[0].isupper() else 'profile'
        embed = discord.Embed(
            color=0xefefef,
            title=f"{user}'s {form}",
            description=None,
            url=u['url']
        )
        contrib_count: Union[tuple, None] = u['contributions']
        orgs_c: int = u['organizations']
        if "bio" in u and u['bio'] is not None and len(u['bio']) > 0:
            embed.add_field(name=":notepad_spiral: Bio:", value=f"```{u['bio']}```")
        occupation: str = f'Works at {u["company"]}\n' if "company" in u and u[
            "company"] is not None else 'Isn\'t part of a company\n'
        orgs: str = f"Belongs to {orgs_c} organizations\n" if orgs_c != 0 else "Doesn't belong to any organizations\n"
        if orgs_c == 1:
            orgs: str = "Belongs to 1 organization\n"
        followers: str = "Isn\'t followed by anyone" if u[
                                                            'followers'] == 0 else f"Has [{u['followers']} followers]({u['url']}?tab=followers)"

        if u['followers'] == 1:
            followers: str = f"Has only [1 follower]({u['url']}?tab=followers)"
        following: str = "doesn't follow anyone, yet" if u[
                                                             'following'] == 0 else f"follows [{u['following']} users]({u['url']}?tab=following)"
        if u['following'] == 1:
            following: str = f"follows only [1 person]({u['url']}?tab=following)"
        follow: str = followers + ' and ' + following

        repos: str = "Has no repositories, yet\n" if u[
                                                         'public_repos'] == 0 else f"Has a total of [{u['public_repos']} repositories]({u['url']}?tab=repositories)\n"
        if u['public_repos'] == 1:
            repos: str = f"Has only [1 repository]({u['url']}?tab=repositories)\n"
        if contrib_count is not None:
            contrib: str = f"\n{contrib_count[0]} contributions this year, {contrib_count[1]} today\n"
        else:
            contrib: str = ""
        info: str = f"Joined GitHub on {datetime.strptime(u['createdAt'], '%Y-%m-%dT%H:%M:%SZ').strftime('%e, %b %Y')}\n{repos}{occupation}{orgs}{follow}{contrib}"
        embed.add_field(name=":mag_right: Info:", value=info, inline=False)
        blog: tuple = (u['websiteUrl'], "Website")
        twitter: tuple = (
            f'https://twitter.com/{u["twitterUsername"]}' if "twitterUsername" in u else None, "Twitter")
        links: list = [blog, twitter]
        link_strings: list = []
        for lnk in links:
            if lnk[0] is not None and len(lnk[0]) != 0:
                link_strings.append(f"- [{lnk[1]}]({lnk[0]})")
        if len(link_strings) != 0:
            embed.add_field(name=f":link: Links:", value='\n'.join(link_strings), inline=False)
        embed.set_thumbnail(url=u['avatarUrl'])
        await ctx.send(embed=embed)

    @commands.cooldown(15, 30, commands.BucketType.user)
    @guild_available()
    @org.command(name='-info', aliases=['-I', '-i', '-Info'])
    async def o_profile_command(self, ctx: commands.Context, *, organization: str) -> None:
        org = await Git.get_org(organization)
        if not org and hasattr(ctx, 'invoked_with_store'):
            await self.client.get_cog('Store').delete_org_field(ctx=ctx)
            await ctx.send(
                f"{self.e}  The organization you had saved has changed its name or was deleted. Please **re-add it** using `git --config -org`")
            return
        if org is None:
            await ctx.send(f"{self.emoji} This organization **doesn't exist!**")
            return None
        form: str = "Profile" if str(organization)[0].isupper() else 'profile'
        embed = discord.Embed(
            color=0xefefef,
            title=f"{organization}'s {form}",
            description=None,
            url=org['html_url']
        )
        mem: list = await Git.get_org_members(organization)
        members: str = f"Has [{len(mem)} public members](https://github.com/orgs/{organization}/people)\n"
        if len(mem) == 1:
            members: str = f"Has only [one public member](https://github.com/orgs/{organization}/people)\n"
        email: str = f"Email: {org['email']}\n" if 'email' in org and org["email"] is not None else '\n'
        if org['description'] is not None and len(org['description']) > 0:
            embed.add_field(name=":notepad_spiral: Description:", value=f"```{org['description']}```")
        repos: str = "Has no repositories, yet\n" if org[
                                                         'public_repos'] == 0 else f"Has a total of [{org['public_repos']} repositories]({org['html_url']})\n"
        if org['public_repos'] == 1:
            repos: str = f"Has only [1 repository]({org['html_url']})\n"
        if org['location'] is not None:
            location: str = f"Is based in {org['location']}\n"
        else:
            location: str = "\n"
        info: str = f"Created on {datetime.strptime(org['created_at'], '%Y-%m-%dT%H:%M:%SZ').strftime('%e, %b %Y')}\n{repos}{members}{location}{email}"
        embed.add_field(name=":mag_right: Info:", value=info, inline=False)
        blog: tuple = (org['blog'], "Website")
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
            embed.add_field(name=f":link: Links:", value='\n'.join(link_strings), inline=False)
        embed.set_thumbnail(url=org['avatar_url'])
        await ctx.send(embed=embed)

    @checkout.command(name='--issue', aliases=['-issue', '-iss', '-issues', '--issues', '-i', 'I', '-I', 'i'])
    @commands.cooldown(10, 30, commands.BucketType.user)
    @guild_available()
    async def issue_command(self, ctx: commands.Context, repo: str, issue_number: str) -> None:
        if not issue_number.isnumeric():
            await ctx.send(f"{self.e}  The second argument must be an issue **number!**")
            return
        issue = await Git.get_issue(repo, int(issue_number))
        if type(issue) is str:
            if issue == 'repo':
                await ctx.send(f"{self.e}  This repository **doesn't exist!**")
                return
            else:
                await ctx.send(f"{self.e}  An issue with this number **doesn't exist!**")
                return
        em: str = f"<:issue_open:788517560164810772>"
        if issue['state'].lower() == 'closed':
            em: str = '<:issue_closed:788517938168594452>'
        embed: discord.Embed = discord.Embed(
            color=0xefefef,
            title=f"{em}  {issue['title']} #{issue_number}",
            description=None,
            url=issue['url']
        )
        if all(['body' in issue, issue['body'], len(issue['body'])]):
            body: Union[str, None] = str(issue['body']).strip()
            if len(body) > 512:
                body: str = re.sub(html_comment_regex, '', body).replace('#', '')[:512]  # Kill comments
                body: str = kill_markdown(f"{body[:body.rindex(' ')]}...".strip())  # Kill markdown
        else:
            body = None
        if body:
            embed.add_field(name=':scroll: Body:', value=f"```{body}```", inline=False)

        created_at: datetime = datetime.strptime(issue['createdAt'], '%Y-%m-%dT%H:%M:%SZ')

        user: str = f"Created by [{issue['author']['login']}]({issue['author']['url']}) \
         on {created_at.strftime('%e, %b %Y')}"

        if issue['closed']:
            closed_at: datetime = datetime.strptime(issue['closedAt'], '%Y-%m-%dT%H:%M:%SZ')
            closed: str = f"\nClosed on {closed_at.strftime('%e, %b %Y')}\n"
        else:
            closed: str = '\n'

        assignees: str = f"{issue['assigneeCount']} assignees"
        if issue['assigneeCount'] == 1:
            assignees: str = 'one assignee'
        elif issue['assigneeCount'] == 0:
            assignees: str = 'no assignees'

        comments: str = f"Has {issue['commentCount']} comments"
        if issue['commentCount'] == 1:
            comments: str = "Has only one comment"
        comments_and_assignees: str = f"{comments} and {assignees}"

        participants: str = f"\n{issue['participantCount']} people have participated in this issue" if \
            issue['participantCount'] != 1 else "\nOne person has participated in this issue"

        info: str = f"{user}{closed}{comments_and_assignees}{participants}"

        embed.add_field(name=':mag_right: Info:', value=info, inline=False)

        if issue['labels']:
            embed.add_field(name=':label: Labels:', value=' '.join([f"`{lb}`" for lb in issue['labels']]))

        embed.set_thumbnail(url=issue['author']['avatarUrl'])
        await ctx.send(embed=embed)


def setup(client):
    client.add_cog(Checkout(client))
