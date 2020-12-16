import discord
from os import getenv
from discord.ext import commands
from ext.decorators import guild_available
from cfg import globals
from motor.motor_asyncio import AsyncIOMotorClient

Git = globals.Git


class Store(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client: commands.Bot = client
        self.db: AsyncIOMotorClient = AsyncIOMotorClient(getenv("DB_CONNECTION")).store.users
        self.emoji: str = '<:github:772040411954937876>'
        self.ga: str = "<:ga:768064843176738816>"
        self.e: str = "<:ge:767823523573923890>"

    @commands.group(name='--config', aliases=['config', '-cfg'])
    @commands.cooldown(15, 30, commands.BucketType.user)
    @guild_available()
    async def config_command(self, ctx: commands.Context) -> None:
        if ctx.invoked_subcommand is None:
            lines: list = ["**In this section you can configure various aspects of your experience**",
                           "\n**Quick access**",
                           "These commands allow you to save a user, repo or org to get with a short command.",
                           "`git config --user {username}` " + self.ga + " Access a saved user with `git --user`",
                           "`git config --org {org}` " + self.ga + " Access a saved organization with `git --org`",
                           "\n**Important!** The command that follows requires the exact syntax of `username/repo-name` in place of the `{repo}` argument, ex. `itsmewulf/GitHub-Discord`",
                           "\n`git config --repo {repo}` " + self.ga + " Access a saved repo with `git --repo`",
                           "\n**You can delete stored data by typing** `git config -delete`"]
            embed = discord.Embed(
                color=0xefefef,
                title=f"{self.emoji}  GitHub Config",
                description='\n'.join(lines)
            )
            await ctx.send(embed=embed)

    @config_command.command(name='--show', aliases=['-S', '-show'])
    @commands.cooldown(15, 30, commands.BucketType.user)
    @guild_available()
    async def config_show(self, ctx: commands.Context) -> None:
        query = await self.db.find_one({"user_id": int(ctx.author.id)})
        if query is None or len(query) == 2:
            await ctx.send(
                f'{self.e}  **You don\'t have any quick access data configured!** Use `git --config` to do it')
            return
        user: str = f"User: `{query['user']}`" if 'user' in query else "User: `Not set`"
        org: str = f"Organization: `{query['org']}`" if 'org' in query else "Organization: `Not set`"
        repo: str = f"Repo: `{query['repo']}`" if 'repo' in query else "Repo: `Not set`"
        data: list = [user, org, repo]
        embed = discord.Embed(
            color=0xefefef,
            title=f"{self.emoji}  Your GitHub Config",
            description="**Quick access:**\n{quick_access}".format(
                quick_access='\n'.join(data))
        )
        await ctx.send(embed=embed)

    @config_command.command(name='--user', aliases=['-U'])
    @commands.cooldown(15, 30, commands.BucketType.user)
    @guild_available()
    async def config_user(self, ctx: commands.Context, *, user: str) -> None:
        u = await Git.get_user(user)
        if u is None:
            await ctx.send(f"{self.e} This user **doesn't exist!**")
            return
        query = await self.db.find_one({"user_id": int(ctx.author.id)})
        if query is not None:
            await self.db.update_one(query, {"$set": {"user": str(user)}})
            await ctx.send(f"{self.emoji}  Quick access user changed to **{user}**")
        else:
            await self.db.insert_one({"user_id": int(ctx.author.id), "user": str(user)})
            await ctx.send(f"{self.emoji}  Quick access user set to **{user}**")

    @config_command.command(name='--org', aliases=['--organization', '-O'])
    @commands.cooldown(15, 30, commands.BucketType.user)
    @guild_available()
    async def config_org(self, ctx: commands.Context, *, org: str) -> None:
        o = await Git.get_org(org)
        if o is None:
            await ctx.send(f"{self.e} This organization **doesn't exist!**")
            return
        query = await self.db.find_one({"user_id": int(ctx.author.id)})
        if query is not None:
            await self.db.update_one(query, {"$set": {"org": str(org)}})
            await ctx.send(f"{self.emoji}  Quick access organization changed to **{org}**")
        else:
            await self.db.insert_one({"user_id": int(ctx.author.id), "org": str(org)})
            await ctx.send(f"{self.emoji}  Quick access organization set to **{org}**")

    @config_command.command(name='--repo', aliases=['--repository', '-R'])
    @commands.cooldown(15, 30, commands.BucketType.user)
    @guild_available()
    async def config_repo(self, ctx, *, repo) -> None:
        r = await Git.get_repo(repo)
        if r is None:
            await ctx.send(f"{self.e} This repository **doesn't exist!**")
            return
        query = await self.db.find_one({"user_id": int(ctx.author.id)})
        if query is not None:
            await self.db.update_one(query, {"$set": {"repo": str(repo)}})
            await ctx.send(f"{self.emoji}  Quick access repo changed to **{repo}**")
        else:
            await self.db.insert_one({"user_id": int(ctx.author.id), "repo": str(repo)})
            await ctx.send(f"{self.emoji}  Quick access repo set to **{repo}**")

    @commands.command(name='--repo', aliases=["-R", '--repository', '-repo'])
    @commands.cooldown(15, 30, commands.BucketType.user)
    @guild_available()
    async def stored_repo_command(self, ctx: commands.Context) -> None:
        store = await self.db.find_one({'user_id': ctx.author.id})
        if store is not None and 'repo' in store:
            ctx.invoked_with_store = True
            await ctx.invoke(self.client.get_command("checkout --repo -info"), repository=str(store["repo"]))
        else:
            await ctx.send(
                f'{self.e}  **You don\'t have a quick access repo configured!** Use `git --config` to do it')

    @commands.command(name='--user', aliases=["-U", '-user'])
    @commands.cooldown(15, 30, commands.BucketType.user)
    @guild_available()
    async def stored_user_command(self, ctx: commands.Context) -> None:
        store = await self.db.find_one({'user_id': ctx.author.id})
        if store is not None and 'user' in store:
            ctx.invoked_with_store = True
            await ctx.invoke(self.client.get_command("checkout --user -info"), user=str(store["user"]))
        else:
            await ctx.send(
                f'{self.e}  **You don\'t have a quick access user configured!** Use `git --config` to do it')

    @commands.command(name='--org', aliases=["--organization", "-O", '-org'])
    @commands.cooldown(15, 30, commands.BucketType.user)
    @guild_available()
    async def stored_org_command(self, ctx: commands.Context) -> None:
        store = await self.db.find_one({'user_id': ctx.author.id})
        if store is not None and 'org' in store:
            ctx.invoked_with_store = True
            await ctx.invoke(self.client.get_command("checkout --org -info"), organization=str(store["org"]))
        else:
            await ctx.send(
                f'{self.e}  **You don\'t have a quick access organization configured!** Use `git --config` to do it')

    @config_command.group(name='-delete', aliases=['-D', '-del', 'delete'])
    @commands.cooldown(15, 30, commands.BucketType.user)
    @guild_available()
    async def delete_field(self, ctx: commands.Context) -> None:
        if ctx.invoked_subcommand is None:
            lines: list = ["**You can delete stored quick access data by running the following commands:**",
                           f"`git config -delete user`" + f' {self.ga} ' + 'delete the quick access user',
                           f"`git config -delete org`" + f' {self.ga} ' + 'delete the quick access organization',
                           f"`git config -delete repo`" + f' {self.ga} ' + 'delete the quick access repo',
                           f"`git config -delete all`" + f' {self.ga} ' + 'delete all of your quick access data']
            embed = discord.Embed(
                color=0xefefef,
                title=f"{self.emoji}  Delete Quick Access Data",
                description='\n'.join(lines)
            )
            await ctx.send(embed=embed)

    @delete_field.command(name='user', aliases=['-U', '-user'])
    @commands.cooldown(15, 30, commands.BucketType.user)
    @guild_available()
    async def delete_user_command(self, ctx: commands.Context):
        query = await self.delete_user_field(ctx=ctx)
        if query:
            await ctx.send(f"{self.emoji}  Saved **user deleted.**")
        else:
            await ctx.send(f"{self.e}  You don't have a user saved!")

    @delete_field.command(name='org', aliases=['-O', '-org', 'organization', '-organization'])
    @commands.cooldown(15, 30, commands.BucketType.user)
    @guild_available()
    async def delete_org_command(self, ctx: commands.Context):
        query = await self.delete_org_field(ctx=ctx)
        if query:
            await ctx.send(f"{self.emoji}  Saved **organization deleted.**")
        else:
            await ctx.send(f"{self.e}  You don't have an organization saved!")

    @delete_field.command(name='repo', aliases=['-R', '-repo'])
    @commands.cooldown(15, 30, commands.BucketType.user)
    @guild_available()
    async def delete_repo_command(self, ctx: commands.Context):
        query = await self.delete_repo_field(ctx=ctx)
        if query:
            await ctx.send(f"{self.emoji}  Saved **repo deleted.**")
        else:
            await ctx.send(f"{self.e}  You don't have a repo saved!")

    @delete_field.command(name='all', aliases=['-A', '-all'])
    @commands.cooldown(15, 30, commands.BucketType.user)
    @guild_available()
    async def delete_entire_record(self, ctx: commands.Context):
        query = await self.db.find_one_and_delete({"user_id": int(ctx.author.id)})
        if not query:
            return await ctx.send(f"{self.e}  It appears that **you don't have anything stored!**")
        await ctx.send(f"{self.emoji}  All of your stored data was **successfully deleted.**")

    async def delete_user_field(self, ctx: commands.Context) -> bool:
        query = await self.db.find_one({"user_id": int(ctx.author.id)})
        copy: dict = dict(query)
        if query is not None and 'user' in query:
            await self.db.update_one(query, {"$unset": {"user": ""}})
            del copy['user']
            if len(copy) == 2:
                await self.db.find_one_and_delete({"user_id": int(ctx.author.id)})
            return True
        return False

    async def delete_org_field(self, ctx: commands.Context) -> bool:
        query = await self.db.find_one({"user_id": int(ctx.author.id)})
        copy: dict = dict(query)
        if query is not None and 'org' in query:
            await self.db.update_one(query, {"$unset": {"org": ""}})
            del copy['org']
            if len(copy) == 2:
                await self.db.find_one_and_delete({"user_id": int(ctx.author.id)})
            return True
        return False

    async def delete_repo_field(self, ctx: commands.Context) -> bool:
        query = await self.db.find_one({"user_id": int(ctx.author.id)})
        copy: dict = dict(query)
        if query is not None and 'repo' in query:
            await self.db.update_one(query, {"$unset": {"repo": ""}})
            del copy['repo']
            if len(copy) == 2:
                await self.db.find_one_and_delete({"user_id": int(ctx.author.id)})
            return True
        return False


def setup(client):
    client.add_cog(Store(client))
