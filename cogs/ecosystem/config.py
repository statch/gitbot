import discord
import asyncio
from discord.ext import commands
from core.globs import Git, Mgr
from typing import Optional


class Config(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot

    @commands.group(name='config', aliases=['--config', '-cfg', 'cfg'])
    @commands.cooldown(15, 30, commands.BucketType.user)
    async def config_command_group(self, ctx: commands.Context) -> None:
        if ctx.invoked_subcommand is None:
            lines: list = [ctx.l.config.default.brief_1,
                           "\n" + ctx.l.config.default.title,
                           ctx.l.config.default.brief_2,
                           "`git config --user {username}` " + Mgr.e.arrow + " " + ctx.l.config.default.commands.user,
                           "`git config --org {org}` " + Mgr.e.arrow + " " + ctx.l.config.default.commands.org,
                           "`git config --repo {repo}` " + Mgr.e.arrow + " " + ctx.l.config.default.commands.repo,
                           "`git config --feed {repo}` " + Mgr.e.arrow + " " + ctx.l.config.default.commands.feed,
                           "\n" + ctx.l.config.default.deletion]
            embed = discord.Embed(
                color=0xefefef,
                title=f"{Mgr.e.github}  GitBot Config",
                description='\n'.join(lines)
            )
            embed.set_footer(text=ctx.l.config.default.footer)
            await ctx.send(embed=embed)

    @config_command_group.command(name='--show', aliases=['-S', '-show', 'show'])
    @commands.cooldown(15, 30, commands.BucketType.user)
    async def config_show(self, ctx: commands.Context) -> None:
        ctx.fmt.set_prefix('config show')
        query: dict = await Mgr.db.users.find_one({"_id": int(ctx.author.id)})
        if not isinstance(ctx.channel, discord.DMChannel):
            release: Optional[dict] = await Mgr.db.guilds.find_one({'_id': ctx.guild.id})
        else:
            release = None
        if query is None and release is None or release and len(release) == 1 and query is None:
            await ctx.err(ctx.l.generic.nonexistent.qa)
            return
        user: str = ctx.fmt('list user', f'`{query["user"]}`' if 'user' in query else f'`{ctx.l.config.show.item_not_set}`')
        org: str = ctx.fmt('list org', f'`{query["org"]}`' if 'org' in query else f'`{ctx.l.config.show.item_not_set}`')
        repo: str = ctx.fmt('list repo', f'`{query["repo"]}`' if 'repo' in query else f'`{ctx.l.config.show.item_not_set}`')
        feed: str = f'{ctx.l.config.show.list.feed}\n' + '\n'.join(
            [f'{Mgr.e.square} `{r["repo"]}`' for r in release['feed']]) if release and release[
            'feed'] else f'{ctx.l.config.show.list.feed} `{ctx.l.config.show.item_not_configured}`'
        data: list = [user, org, repo, feed]
        embed = discord.Embed(
            color=0xefefef,
            title=f"{Mgr.e.github}  {ctx.l.config.show.title}",
            description=f"{ctx.l.config.show.heading}\n" + '\n'.join(data)
        )
        await ctx.send(embed=embed)

    @config_command_group.command(name='feed', aliases=['-feed', '--feed', 'release', '-release', '--release', '-f', '-F'])
    @commands.guild_only()
    @commands.has_guild_permissions(manage_channels=True)
    @commands.bot_has_guild_permissions(manage_webhooks=True, manage_channels=True)
    @commands.cooldown(10, 30, commands.BucketType.guild)
    async def config_release_feed(self, ctx: commands.Context, repo: Optional[str] = None) -> None:
        ctx.fmt.set_prefix('config feed')
        g: dict = await Mgr.db.guilds.find_one({'_id': ctx.guild.id})
        if not g:
            embed: discord.Embed = discord.Embed(
                color=0xff009b,
                title=ctx.l.config.feed.embeds.start.title,
                description=ctx.l.config.feed.embeds.start.description
            )
            embed.set_footer(text=ctx.l.config.feed.embeds.start.footer)
            base_msg: discord.Message = await ctx.send(embed=embed)
            while True:
                try:
                    msg: discord.Message = await self.bot.wait_for('message',
                                                                   check=lambda msg_: (msg_.channel.id == ctx.channel.id
                                                                                       and msg_.author.id == ctx.author.id),
                                                                   timeout=30)
                    if (m := msg.content.lower()) == 'cancel':
                        await base_msg.delete()
                        await ctx.err(ctx.l.config.feed.cancelled)
                        return
                    elif m == 'create':
                        channel: Optional[discord.TextChannel] = await ctx.guild.create_text_channel('release-feeds',
                                                                                                     topic=f'Release feeds of configured repos will show up here!')
                    else:
                        try:
                            channel: Optional[discord.TextChannel] = await commands.TextChannelConverter().convert(ctx,
                                                                                                                   msg.content)
                        except commands.BadArgument:
                            await ctx.err(ctx.l.config.feed.invalid_channel)
                            continue
                    hook: discord.Webhook = await channel.create_webhook(name=self.bot.user.name,
                                                                         reason=f'Release Feed channel setup by {ctx.author}')
                    feed: list = []
                    r: Optional[dict] = None
                    if repo:
                        r: dict = await Git.get_latest_release(repo)
                        feed = [{'repo': repo.lower(), 'release': r['release']['tagName']}] if r and r[
                            'release'] else []
                    if hook:
                        await Mgr.db.guilds.insert_one(
                            {'_id': ctx.guild.id, 'hook': hook.url[33:], 'feed': feed if feed else []})
                        success_embed: discord.Embed = discord.Embed(
                            color=0x33ba7c,
                            title=ctx.l.config.feed.embeds.success.title,
                            description=ctx.l.config.feed.embeds.success.description
                        )
                        if r:
                            success_embed.set_footer(text=ctx.fmt('embeds success footer', repo))
                        try:
                            await msg.delete()
                        except discord.errors.Forbidden:
                            pass
                        await base_msg.edit(embed=success_embed)
                        return
                    await base_msg.delete()
                    await ctx.err(ctx.l.generic.unspecified)
                    return
                except asyncio.TimeoutError:
                    timeout_embed = discord.Embed(
                        color=0xffd500,
                        title=ctx.l.config.feed.embeds.timeout.title
                    )
                    timeout_embed.set_footer(text=ctx.l.config.feed.embeds.timeout.footer)
                    await base_msg.edit(embed=timeout_embed)
                    return
        if g and not repo:
            await ctx.err(ctx.l.config.feed.no_arg)
            return
        r: dict = await Git.get_latest_release(repo)
        if not r:
            await ctx.err(ctx.l.generic.nonexistent.repo.base)
        if g:
            for r_ in g['feed']:
                if r_['repo'].lower() == repo.lower():
                    await ctx.err(ctx.l.config.feed.already_logged)
                    return
            if len(g['feed']) < 3:
                await Mgr.db.guilds.update_one({'_id': ctx.guild.id},
                                               {'$push': {'feed': {'repo': repo, 'release': r['release']['tagName'] if r['release'] else None}}})
                await ctx.err(ctx.fmt('success', repo))
            else:
                embed_limit_reached: discord.Embed = discord.Embed(
                    color=0xda4353,
                    title=ctx.l.config.feed.embeds.limit_reached.title,
                    description=ctx.l.config.feed.embeds.limit_reached.description
                )
                embed_limit_reached.set_footer(text=ctx.l.config.feed.embeds.limit_reached.footer,
                                               icon_url=self.bot.user.avatar_url)
                await ctx.send(embed=embed_limit_reached)

    @config_command_group.command(name='--user', aliases=['-u', '-user', 'user'])
    @commands.cooldown(15, 30, commands.BucketType.user)
    async def config_user(self, ctx: commands.Context, user: str) -> None:
        u = await Mgr.db.users.setitem(ctx, 'user', user)
        if u:
            await ctx.send(f"{Mgr.e.github}  Quick access user set to **{user}**")
        else:
            await ctx.send(f'{Mgr.e.err}  This user **doesn\'t exist!**')

    @config_command_group.command(name='--org', aliases=['--organization', '-O', '-org', 'org'])
    @commands.cooldown(15, 30, commands.BucketType.user)
    async def config_org(self, ctx: commands.Context, org: str) -> None:
        o = await Mgr.db.users.setitem(ctx, 'org', org)
        if o:
            await ctx.send(f"{Mgr.e.github}  Quick access organization set to **{org}**")
        else:
            await ctx.send(f'{Mgr.e.err}  This organization **doesn\'t exist!**')

    @config_command_group.command(name='--repo', aliases=['--repository', '-R', '-repo', 'repo'])
    @commands.cooldown(15, 30, commands.BucketType.user)
    async def config_repo(self, ctx, repo) -> None:
        r = await Mgr.db.users.setitem(ctx, 'repo', repo)
        if r:
            await ctx.send(f"{Mgr.e.github}  Quick access repo set to **{repo}**")
        else:
            await ctx.send(f'{Mgr.e.err}  This repo **doesn\'t exist!**')

    @config_command_group.group(name='-delete', aliases=['-D', '-del', 'delete', '--delete'])
    @commands.cooldown(15, 30, commands.BucketType.user)
    async def delete_field_group(self, ctx: commands.Context) -> None:
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(
                color=0xefefef,
                title=f"{Mgr.e.github}  Delete Quick Access Data",
                description=f"**You can delete stored quick access data by running the following commands:**\n"
                            f"`git config --delete user` {Mgr.e.arrow} delete the quick access user\n"
                            f"`git config --delete org` {Mgr.e.arrow} delete the quick access organization\n"
                            f"`git config --delete repo` {Mgr.e.arrow} delete the quick access repo\n"
                            f"`git config --delete all` {Mgr.e.arrow} delete all of your quick access data\n"
                            f"`git config --delete feed` {Mgr.e.arrow} view options regarding deleting release feed data"
            )
            await ctx.send(embed=embed)

    @delete_field_group.group(name='feed', aliases=['-feed', '--feed'], invoke_without_command=True)
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True, manage_channels=True)
    @commands.cooldown(15, 30, commands.BucketType.guild)
    async def delete_feed_group(self, ctx: commands.Context, repo: Optional[str]) -> None:
        if ctx.invoked_subcommand is None:
            if not repo:
                embed: discord.Embed = discord.Embed(
                    color=0xefefef,
                    title='Delete Release Feed data',
                    description=f'**You can delete stored release feed data by running the following commands:**\n'
                                f'`git config -delete feed {{repo}}` {Mgr.e.arrow} unsubscribe from a specific repo\n'
                                f'`git config -delete feed all` {Mgr.e.arrow} unsubscribe from all repos\n'
                                f'`git config -delete feed total` {Mgr.e.arrow} unsubscribe from all releases and delete '
                                f'the '
                                f'feed webhook'
                )
                await ctx.send(embed=embed)
            else:
                guild: Optional[dict] = await Mgr.db.guilds.find_one({'_id': ctx.guild.id})
                if guild:
                    for r in guild['feed']:
                        if r['repo'].lower() == repo.lower():
                            guild['feed'].remove(r)
                            await Mgr.db.guilds.update_one({'_id': ctx.guild.id}, {'$set': {'feed': guild['feed']}})
                            await ctx.send(f'{Mgr.e.github}  `{repo}`\'s releases will **no longer be logged.**')
                            return
                    await ctx.send(f'{Mgr.e.err}  That repo\'s releases are **not currently logged!**')
                else:
                    await ctx.send(f'{Mgr.e.err}  You don\'t have a release feed channel configured!')

    @delete_feed_group.command(name='all', aliases=['-all', '--all'])
    @commands.guild_only()
    @commands.cooldown(15, 30, commands.BucketType.guild)
    @commands.has_guild_permissions(manage_guild=True, manage_channels=True)
    async def delete_all_feeds_command(self, ctx: commands.Context) -> None:
        guild: Optional[dict] = await Mgr.db.guilds.find_one({'_id': ctx.guild.id})
        if guild is None:
            await ctx.send(f'{Mgr.e.err}  You don\'t have a release feed configured, so **nothing was deleted.**')
        else:
            if guild['feed']:
                await Mgr.db.guilds.update_one(guild, {'$set': {'feed': []}})
            await ctx.send(f'{Mgr.e.github}  All release feeds were **closed successfully.**')

    @delete_feed_group.command(name='total', aliases=['-total', '--total', '-t'])
    @commands.guild_only()
    @commands.cooldown(10, 30, commands.BucketType.guild)
    @commands.has_guild_permissions(manage_guild=True, manage_channels=True)
    @commands.bot_has_guild_permissions()
    async def delete_feed_with_channel_command(self, ctx: commands.Context) -> None:
        guild: Optional[dict] = await Mgr.db.guilds.find_one({'_id': ctx.guild.id})
        if guild is None:
            await ctx.send(f'{Mgr.e.err}  You don\'t have a release feed configured, so **nothing was deleted.**')
        else:
            await Mgr.db.guilds.delete_one(guild)
            try:
                webhook: discord.Webhook = discord.Webhook.from_url('https://discord.com/api/webhooks/' + guild['hook'],
                                                                    adapter=discord.AsyncWebhookAdapter(Git.ses))
                await webhook.delete()
            except (discord.NotFound, discord.HTTPException):
                pass
            finally:
                await ctx.send(f'{Mgr.e.err}  The release feed channel has been **closed successfully.**')

    @delete_field_group.command(name='user', aliases=['-U', '-user', '--user'])
    @commands.cooldown(15, 30, commands.BucketType.user)
    async def delete_user_command(self, ctx: commands.Context) -> None:
        deleted: bool = await Mgr.db.users.delitem(ctx, 'user')
        if deleted:
            await ctx.send(f"{Mgr.e.github}  Saved **user deleted.**")
        else:
            await ctx.send(f"{Mgr.e.err}  You don't have a user saved!")

    @delete_field_group.command(name='org', aliases=['-O', '-org', 'organization', '-organization'])
    @commands.cooldown(15, 30, commands.BucketType.user)
    async def delete_org_command(self, ctx: commands.Context) -> None:
        deleted: bool = await Mgr.db.users.delitem(ctx, 'org')
        if deleted:
            await ctx.send(f"{Mgr.e.github}  Saved **organization deleted.**")
        else:
            await ctx.send(f"{Mgr.e.err}  You don't have an organization saved!")

    @delete_field_group.command(name='repo', aliases=['-R', '-repo'])
    @commands.cooldown(15, 30, commands.BucketType.user)
    async def delete_repo_command(self, ctx: commands.Context) -> None:
        deleted: bool = await Mgr.db.users.delitem(ctx, 'repo')
        if deleted:
            await ctx.send(f"{Mgr.e.github}  Saved **repo deleted.**")
        else:
            await ctx.send(f"{Mgr.e.err}  You don't have a repo saved!")

    @delete_field_group.command(name='all', aliases=['-A', '-all'])
    @commands.cooldown(15, 30, commands.BucketType.user)
    async def delete_entire_record(self, ctx: commands.Context) -> None:
        query: dict = await Mgr.db.users.find_one_and_delete({"_id": int(ctx.author.id)})
        if not query:
            await ctx.send(f"{Mgr.e.err}  It appears that **you don't have anything stored!**")
            return
        await ctx.send(f"{Mgr.e.github}  All of your stored data was **successfully deleted.**")


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Config(bot))
