import discord
import discord.ext.commands as commands
import re
from cfg import config
from typing import Union
from datetime import datetime

Git = config.Git
md_emoji_re = re.compile(r':.*:', re.IGNORECASE)
PR_STATES: dict = {
    "open": "<:pr_open:795793711312404560>",
    "closed": "<:pr_closed:788518707969785886>",
    "merged": "<:merge:795801508146839612>"
}


class Checkout(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.emoji: str = '<:github:772040411954937876>'
        self.square: str = ":white_small_square:"
        self.f: str = "<:file:762378114135097354>"
        self.fd: str = "<:folder:762378091497914398>"
        self.e: str = "<:ge:767823523573923890>"

    @commands.group(name='checkout', aliases=['c', '-C'])
    async def checkout(self, ctx: commands.Context) -> None:
        if ctx.invoked_subcommand is None:
            await ctx.send(
                f"{self.emoji} Looks like you're lost! **Use the command** `git --help` **to get back on track.**")

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
            more: str = str(len(files) - 15) if len(files) - 15 < 15 else "15+"
            embed.set_footer(text=f"View {more} more on GitHub")
        await ctx.send(embed=embed)

    @repo.command(name="-info", aliases=['-I', '-i', '-Info'])
    @commands.cooldown(15, 30, commands.BucketType.user)
    async def repo_info_command(self, ctx: commands.Context, *, repository: str) -> None:
        r: Union[dict, None] = await Git.get_repo(str(repository))
        if not r:
            if hasattr(ctx, 'invoked_with_store'):
                await self.bot.get_cog('Store').delete_repo_field(ctx=ctx)
                await ctx.send(
                    f"{self.e}  The repository you had saved changed its name or was deleted. Please **re-add it** "
                    f"using `git --config -repo`")
            else:
                await ctx.send(f"{self.emoji} This repository **doesn't exist!**")
            return None

        embed = discord.Embed(
            color=int(r['primaryLanguage']['color'][1:], 16) if r['primaryLanguage'] else 0xefefef,
            title=f"{repository}",
            description=None,
            url=r['url']
        )

        watch: int = r['watchers']['totalCount']
        star: int = r['stargazers']['totalCount']
        open_issues: int = r['issues']['totalCount']

        if r['description'] is not None and len(r['description']) != 0:
            embed.add_field(name=":notepad_spiral: Description:",
                            value=f"```{re.sub(md_emoji_re, '', r['description']).strip()}```")

        watchers: str = f"Has [{watch} watchers]({r['url']}/watchers)" if watch != 1 else f"Has [one watcher]({r['url']}/watchers) "
        if watch == 0:
            watchers: str = f"Has no watchers"
        stargazers: str = f"no stargazers\n" if star == 0 else f"[{star} stargazers]({r['url']}/stargazers)\n"
        if star == 1:
            stargazers: str = f"[one stargazer]({r['url']}/stargazers)\n"

        watchers_stargazers: str = f"{watchers} and {stargazers}"

        issues: str = f'Doesn\'t have any [open issues]({r["url"]}/issues)\n' if open_issues == 0 else f"Has [{open_issues} open issues]({r['url']}/issues)\n"
        if open_issues == 1:
            issues: str = f"Has only one [open issue]({r['url']}/issues)\n"

        forks: str = f"No one has forked this repo, yet\n" if r[
                                                                  'forkCount'] == 0 else f"Has been forked [{r['forkCount']} times]({r['url']}/network/members)\n"
        if r['forkCount'] == 1:
            forks: str = f"It's been forked [only once]({r['url']}/network/members)\n"
        forked = ""
        if 'isFork' in r and r['isFork'] is True:
            forked = f"This repo is a fork of [{r['parent']['nameWithOwner']}]({r['parent']['url']})\n"

        created_at = f"Created on {datetime.strptime(r['createdAt'], '%Y-%m-%dT%H:%M:%SZ').strftime('%e, %b %Y')}\n"

        languages = ""
        if lang := r['primaryLanguage']:
            if r['languages'] == 1:
                languages = f'Written mainly using {lang["name"]}'
            else:
                languages = f'Written in {r["languages"]} languages, mainly in {lang["name"]}'

        info: str = f"{created_at}{issues}{forks}{watchers_stargazers}{forked}{languages}"
        embed.add_field(name=":mag_right: Info:", value=info, inline=False)

        homepage: tuple = (r['homepageUrl'] if 'homepageUrl' in r and r['homepageUrl'] else None, "Homepage")
        links: list = [homepage]
        link_strings: list = []
        for lnk in links:
            if lnk[0] is not None and len(lnk[0]) != 0:
                link_strings.append(f"- [{lnk[1]}]({lnk[0]})")
        if len(link_strings) != 0:
            embed.add_field(name=f":link: Links:", value='\n'.join(link_strings), inline=False)

        if r['topics'][0] and len(r['topics'][0]) > 1:
            topic_strings = ' '.join(
                [f"[`{t['topic']['name']}`]({t['url']})" for t in r['topics'][0]])
            more = f' `+{r["topics"][1] - 10}`' if r["topics"][1] > 10 else ""
            embed.add_field(name=f':label: Topics:', value=topic_strings + more)

        if r['graphic']:
            embed.set_image(url=r['graphic'])

        if 'licenseInfo' in r and r['licenseInfo'] is not None and r['licenseInfo']["name"].lower() != 'other':
            embed.set_footer(text=f'Licensed under the {r["licenseInfo"]["name"]}')

        await ctx.send(embed=embed)

    @commands.cooldown(15, 30, commands.BucketType.user)
    @user.command(name='-info', aliases=['-I', '-i', '-Info'])
    async def profile_command(self, ctx: commands.Context, *, user: str) -> None:
        u = await Git.get_user(user)
        if not u:
            if hasattr(ctx, 'invoked_with_store'):
                await self.bot.get_cog('Store').delete_user_field(ctx=ctx)
                await ctx.send(
                    f"{self.e}  The user you had saved has changed their name or deleted their account. Please "
                    f"**re-add them** using `git --config -user`")
            else:
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
    @org.command(name='-info', aliases=['-I', '-i', '-Info'])
    async def o_profile_command(self, ctx: commands.Context, *, organization: str) -> None:
        org = await Git.get_org(organization)
        if not org:
            if hasattr(ctx, 'invoked_with_store'):
                await self.bot.get_cog('Store').delete_org_field(ctx=ctx)
                await ctx.send(
                    f"{self.e}  The organization you had saved has changed its name or was deleted. Please **re-add it** using `git --config -org`")
            else:
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
    async def issue_command(self, ctx: commands.Context, repo: str, issue_number: str) -> None:
        if not issue_number.isnumeric():
            await ctx.send(f"{self.e}  The second argument must be an issue **number!**")
            return
        issue = await Git.get_issue(repo, int(issue_number))
        if isinstance(issue, str):
            if issue == 'repo':
                await ctx.send(f"{self.e}  This repository **doesn't exist!**")
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
                body: str = body[:512]
                body: str = f"{body[:body.rindex(' ')]}...".strip()
        else:
            body = None
        if body:
            embed.add_field(name=':notepad_spiral: Body:', value=f"```{body}```", inline=False)

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
        elif issue['commentCount'] == 0:
            comments: str = "Has no comments"

        comments_and_assignees: str = f"{comments} and {assignees}"

        participants: str = f"\n{issue['participantCount']} people have participated in this issue" if \
            issue['participantCount'] != 1 else "\nOne person has participated in this issue"

        info: str = f"{user}{closed}{comments_and_assignees}{participants}"

        embed.add_field(name=':mag_right: Info:', value=info, inline=False)

        if issue['labels']:
            embed.add_field(name=':label: Labels:', value=' '.join([f"`{lb}`" for lb in issue['labels']]))

        embed.set_thumbnail(url=issue['author']['avatarUrl'])
        await ctx.send(embed=embed)

    @checkout.command(name='--pr', aliases=['--pull', '-pr', 'pr', '--pullrequest', '-pull'])
    @commands.cooldown(10, 30, commands.BucketType.user)
    async def pull_request_command(self, ctx: commands.Context, repo: str, pr_number: str):
        if not pr_number.isnumeric():
            await ctx.send(f"{self.e}  The second argument must be a pull request **number!**")
            return
        pr: dict = await Git.get_pull_request(repo, int(pr_number))
        if isinstance(pr, str):
            if pr == 'repo':
                await ctx.send(f"{self.e}  This repository **doesn't exist!**")
            else:
                await ctx.send(f"{self.e}  A pull request with this number **doesn't exist!**")
            return

        title: str = pr['title'] if len(pr['title']) <= 90 else f"{pr['title'][:87]}..."
        state = pr['state'].lower().capitalize()
        embed: discord.Embed = discord.Embed(
            title=f"{PR_STATES[state.lower()]}  {title} #{pr_number}",
            url=pr['url'],
            color=0xefefef,
            description=None
        )
        embed.set_thumbnail(url=pr['author']['avatarUrl'])
        if all(['bodyText' in pr and pr['bodyText'], len(pr['bodyText'])]):
            body = pr['bodyText']
            if len(body) > 390:
                body: str = body[:387]
                body: str = f"{body[:body.rindex(' ')]}...".strip()
            embed.add_field(name=':notepad_spiral: Body:', value=f"```{body}```", inline=False)

        created_at: datetime = datetime.strptime(pr['createdAt'], '%Y-%m-%dT%H:%M:%SZ')
        user: str = f"Created by [{pr['author']['login']}]({pr['author']['url']}) on {created_at.strftime('%e, %b %Y')}"

        if pr['closed']:
            closed_at: datetime = datetime.strptime(pr['closedAt'], '%Y-%m-%dT%H:%M:%SZ')
            closed: str = f"\nClosed on {closed_at.strftime('%e, %b %Y')}\n"
        else:
            closed: str = '\n'

        reviews: str = f"{pr['reviews']['totalCount']} reviews"
        if pr['reviews']['totalCount'] == 1:
            reviews: str = 'one review'
        elif pr['reviews']['totalCount'] == 0:
            reviews: str = 'no reviews'

        comments: str = f"Has {pr['comments']['totalCount']} comments"
        if pr['comments']['totalCount'] == 1:
            comments: str = "Has only one comment"
        elif pr['comments']['totalCount'] == 0:
            comments: str = 'Has no comments'

        comments_and_reviews: str = f'{comments} and {reviews}\n'

        commit_c: int = pr["commits"]["totalCount"]
        commits = f'[{commit_c} commits]({pr["url"]}/commits)'
        if commit_c == 1:
            commits = f'[one commit]({pr["url"]}/commits)'

        files_changed: str = f'[{pr["changedFiles"]} files]({pr["url"]}/files) ' \
                             f'have been changed in {commits}\n'
        if pr["changedFiles"] == 1:
            files_changed: str = f'[One file]({pr["url"]}/files) was changed ' \
                                 f'in [{commit_c} commits]({pr["url"]}/commits)\n'
        elif pr['changedFiles'] == 0:
            files_changed: str = f'No files have been changed in this PR\n'

        additions: str = f'Updated with {pr["additions"]} additions'
        if pr["additions"] == 1:
            additions: str = 'Updated with one addition'
        elif pr['additions'] == 0:
            additions: str = 'Updated with no additions'

        deletions: str = f'{pr["deletions"]} deletions'
        if pr['deletions'] == 1:
            deletions: str = 'one deletion'
        elif pr['deletions'] == 0:
            deletions: str = 'no deletions'

        additions_and_deletions: str = f'{additions} and {deletions}.\n'

        assignee_strings = [f"- [{u[0]}]({u[1]})\n" for u in pr['assignees']['users']]
        reviewer_strings = [f"- [{u[0]}]({u[1]})\n" for u in pr['reviewers']['users']]
        participant_strings = [f"- [{u[0]}]({u[1]})\n" for u in pr['participants']['users']]

        assignee_strings = assignee_strings if len(assignee_strings) <= 3 else assignee_strings[
                                                                               :3] + f'- and {len(assignee_strings) - 3} more'

        reviewer_strings = reviewer_strings if len(reviewer_strings) <= 3 else reviewer_strings[
                                                                               :3] + f'- and {len(reviewer_strings) - 3} more'

        participant_strings = participant_strings if len(participant_strings) <= 3 else participant_strings[
                                                                                        :3] + f'- and {len(participant_strings)} more'

        cross_repo: str = f'This pull request came from a fork.' if pr['isCrossRepository'] else ''
        info: str = f'{user}{closed}{comments_and_reviews}{files_changed}{additions_and_deletions}{cross_repo}'
        embed.add_field(name=':mag_right: Info:', value=info, inline=False)

        embed.add_field(name='Participants:',
                        value=''.join(participant_strings) if participant_strings else f'No participants',
                        inline=True)
        embed.add_field(name='Assignees:',
                        value=''.join(assignee_strings) if assignee_strings else f'No assignees',
                        inline=True)
        embed.add_field(name='Reviewers:',
                        value=''.join(reviewer_strings) if reviewer_strings else f'No reviewers',
                        inline=True)

        if pr['labels']:
            embed.add_field(name=':label: Labels:', value=' '.join([f"`{lb}`" for lb in pr['labels']]), inline=False)

        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Checkout(bot))
