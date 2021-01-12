import discord
import os
from discord.ext import commands
from core import bot_config
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient

Git = bot_config.Git


class Config(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot
        self.db: AsyncIOMotorClient = AsyncIOMotorClient(os.getenv('DB_CONNECTION')).store.users
        self.emoji: str = '<:github:772040411954937876>'
        self.ga: str = '<:ga:768064843176738816>'
        self.e: str = '<:ge:767823523573923890>'

    @commands.group(name='config', aliases=['--config', '-cfg', 'cfg'])
    @commands.cooldown(15, 30, commands.BucketType.user)
    async def config_command_group(self, ctx: commands.Context) -> None:
        if ctx.invoked_subcommand is None:
            lines: list = ["**In this section you can configure various aspects of your experience**",
                           "\n**Quick access**",
                           "These commands allow you to save a user, repo or org to get with a short command.",
                           "`git config --user {username}` " + self.ga + " Access a saved user with `git --user`",
                           "`git config --org {org}` " + self.ga + " Access a saved organization with `git --org`",
                           "`git config --repo {repo}` " + self.ga + " Access a saved repo with `git --repo`",
                           "\n**You can delete stored data by typing** `git config --delete`"]
            embed = discord.Embed(
                color=0xefefef,
                title=f"{self.emoji}  GitBot Config",
                description='\n'.join(lines)
            )
            embed.set_footer(text='To see what you have saved, use git config --show')
            await ctx.send(embed=embed)

    @config_command_group.command(name='--show', aliases=['-S', '-show', 'show'])
    @commands.cooldown(15, 30, commands.BucketType.user)
    async def config_show(self, ctx: commands.Context) -> None:
        query = await self.db.find_one({"user_id": int(ctx.author.id)})
        if query is None or len(query) == 2:
            await ctx.send(
                f'{self.e}  **You don\'t have any quick access data configured!** Use `git config` to do it')
            return
        user: str = f"User: `{query['user']}`" if 'user' in query else "User: `Not set`"
        org: str = f"Organization: `{query['org']}`" if 'org' in query else "Organization: `Not set`"
        repo: str = f"Repo: `{query['repo']}`" if 'repo' in query else "Repo: `Not set`"
        data: list = [user, org, repo]
        embed = discord.Embed(
            color=0xefefef,
            title=f"{self.emoji}  Your {self.bot.user.name} Config",
            description="**Quick access:**\n{quick_access}".format(
                quick_access='\n'.join(data))
        )
        await ctx.send(embed=embed)

    @config_command_group.command(name='--user', aliases=['-u', '-user'])
    @commands.cooldown(15, 30, commands.BucketType.user)
    async def config_user(self, ctx: commands.Context, user: str) -> None:
        u = await self.setitem(ctx, 'user', user)
        if u:
            await ctx.send(f"{self.emoji}  Quick access user set to **{user}**")
        else:
            await ctx.send(f'{self.e}  This user **doesn\'t exist!**')

    @config_command_group.command(name='--org', aliases=['--organization', '-O', '-org'])
    @commands.cooldown(15, 30, commands.BucketType.user)
    async def config_org(self, ctx: commands.Context, org: str) -> None:
        o = await self.setitem(ctx, 'org', org)
        if o:
            await ctx.send(f"{self.emoji}  Quick access organization set to **{org}**")
        else:
            await ctx.send(f'{self.e}  This organization **doesn\'t exist!**')

    @config_command_group.command(name='--repo', aliases=['--repository', '-R', '-repo'])
    @commands.cooldown(15, 30, commands.BucketType.user)
    async def config_repo(self, ctx, repo) -> None:
        r = await self.setitem(ctx, 'repo', repo)
        if r:
            await ctx.send(f"{self.emoji}  Quick access repo set to **{repo}**")
        else:
            await ctx.send(f'{self.e}  This repo **doesn\'t exist!**')

    @config_command_group.group(name='-delete', aliases=['-D', '-del', 'delete', '--delete'])
    @commands.cooldown(15, 30, commands.BucketType.user)
    async def delete_field_group(self, ctx: commands.Context) -> None:
        if ctx.invoked_subcommand is None:
            lines: list = ["**You can delete stored quick access data by running the following commands:**",
                           f"`git config --delete user`" + f' {self.ga} ' + 'delete the quick access user',
                           f"`git config --delete org`" + f' {self.ga} ' + 'delete the quick access organization',
                           f"`git config --delete repo`" + f' {self.ga} ' + 'delete the quick access repo',
                           f"`git config --delete all`" + f' {self.ga} ' + 'delete all of your quick access data']
            embed = discord.Embed(
                color=0xefefef,
                title=f"{self.emoji}  Delete Quick Access Data",
                description='\n'.join(lines)
            )
            await ctx.send(embed=embed)

    @delete_field_group.command(name='user', aliases=['-U', '-user'])
    @commands.cooldown(15, 30, commands.BucketType.user)
    async def delete_user_command(self, ctx: commands.Context) -> None:
        deleted = await self.delete_field_group(ctx, 'user')
        if deleted:
            await ctx.send(f"{self.emoji}  Saved **user deleted.**")
        else:
            await ctx.send(f"{self.e}  You don't have a user saved!")

    @delete_field_group.command(name='org', aliases=['-O', '-org', 'organization', '-organization'])
    @commands.cooldown(15, 30, commands.BucketType.user)
    async def delete_org_command(self, ctx: commands.Context) -> None:
        deleted = await self.delete_field_group(ctx, 'org')
        if deleted:
            await ctx.send(f"{self.emoji}  Saved **organization deleted.**")
        else:
            await ctx.send(f"{self.e}  You don't have an organization saved!")

    @delete_field_group.command(name='repo', aliases=['-R', '-repo'])
    @commands.cooldown(15, 30, commands.BucketType.user)
    async def delete_repo_command(self, ctx: commands.Context) -> None:
        deleted = await self.delete_field_group(ctx, 'repo')
        if deleted:
            await ctx.send(f"{self.emoji}  Saved **repo deleted.**")
        else:
            await ctx.send(f"{self.e}  You don't have a repo saved!")

    @delete_field_group.command(name='all', aliases=['-A', '-all'])
    @commands.cooldown(15, 30, commands.BucketType.user)
    async def delete_entire_record(self, ctx: commands.Context) -> None:
        query = await self.db.find_one_and_delete({"user_id": int(ctx.author.id)})
        if not query:
            await ctx.send(f"{self.e}  It appears that **you don't have anything stored!**")
            return
        await ctx.send(f"{self.emoji}  All of your stored data was **successfully deleted.**")

    async def delete_field(self, ctx: commands.Context, field: str) -> bool:
        query = await self.db.find_one({"user_id": ctx.author.id})
        if query is not None and field in query:
            await self.db.update_one(query, {"$unset": {field: ""}})
            del query[field]
            if len(query) == 2:
                await self.db.find_one_and_delete({"user_id": ctx.author.id})
            return True
        return False

    async def getitem(self, ctx: commands.Context, item: str) -> Optional[str]:
        query = await self.db.find_one({'user_id': ctx.author.id})
        if query and item in query:
            return query[item]
        return None

    async def setitem(self, ctx: commands.Context, item: str, value: str) -> bool:
        exists = await ({'user': Git.get_user, 'repo': Git.get_repo, 'org': Git.get_org}[item])(value) is not None
        if exists:
            query = await self.db.find_one({"user_id": ctx.author.id})
            if query is not None:
                await self.db.update_one(query, {"$set": {item: value}})
            else:
                await self.db.insert_one({"user_id": ctx.author.id, item: value})
            return True
        return False


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Config(bot))
