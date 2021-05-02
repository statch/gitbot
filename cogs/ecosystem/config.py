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
                           f"`git config --user {{{ctx.l.argument_placeholders.user}}}` " + Mgr.e.arrow + " " + ctx.l.config.default.commands.user,
                           f"`git config --org {{{ctx.l.argument_placeholders.org}}}` " + Mgr.e.arrow + " " + ctx.l.config.default.commands.org,
                           f"`git config --repo {{{ctx.l.argument_placeholders.repo}}}` " + Mgr.e.arrow + " " + ctx.l.config.default.commands.repo,
                           f"`git config --feed {{{ctx.l.argument_placeholders.repo}}}` " + Mgr.e.arrow + " " + ctx.l.config.default.commands.feed,
                           "\n" + ctx.l.config.default.deletion]
            embed = discord.Embed(
                color=0xefefef,
                title=f"{Mgr.e.github}  {ctx.l.config.default.embed_title}",
                description='\n'.join(lines)
            )
            embed.set_footer(text=ctx.l.config.default.footer)
            await ctx.send(embed=embed)

    @config_command_group.command(name='--show', aliases=['-S', '-show', 'show'])
    @commands.cooldown(15, 30, commands.BucketType.user)
    async def config_show_command(self, ctx: commands.Context) -> None:
        ctx.fmt.set_prefix('config show')
        query: dict = await Mgr.db.users.find_one({"_id": int(ctx.author.id)})
        if not isinstance(ctx.channel, discord.DMChannel):
            release: Optional[dict] = await Mgr.db.guilds.find_one({'_id': ctx.guild.id})
        else:
            release = None
        if query is None and release is None or release and len(release) == 1 and query is None:
            await ctx.err(ctx.l.generic.nonexistent.qa)
            return
        lang: str = ctx.fmt('accessibility list locale', f'`{ctx.l.meta.localized_name.capitalize()}`')
        user: str = ctx.fmt('qa list user', f'`{query["user"]}`' if 'user' in query else f'`{ctx.l.config.show.item_not_set}`')
        org: str = ctx.fmt('qa list org', f'`{query["org"]}`' if 'org' in query else f'`{ctx.l.config.show.item_not_set}`')
        repo: str = ctx.fmt('qa list repo', f'`{query["repo"]}`' if 'repo' in query else f'`{ctx.l.config.show.item_not_set}`')
        feed: str = f'{ctx.l.config.show.guild.list.feed}\n' + '\n'.join(
            [f'{Mgr.e.square} `{r["repo"]}`' for r in release['feed']]) if release and release[
            'feed'] else f'{ctx.l.config.show.guild.list.feed} `{ctx.l.config.show.item_not_configured}`'
        accessibility: list = ctx.l.config.show.accessibility.heading + '\n' + '\n'.join([lang])
        qa: list = ctx.l.config.show.qa.heading + '\n' + '\n'.join([user, org, repo])
        guild: list = ctx.l.config.show.guild.heading + '\n' + '\n'.join([feed])
        shortest_heading_len: int = min(map(len, [ctx.l.config.show.accessibility.heading,
                                                  ctx.l.config.show.guild.heading,
                                                  ctx.l.config.show.qa.heading]))
        linebreak: str = f'\n{"⎯" * shortest_heading_len}\n'
        embed = discord.Embed(
            color=0xefefef,
            title=f"{Mgr.e.github}  {ctx.l.config.show.title}",
            description=f"{accessibility}{linebreak}{qa}{linebreak}{guild}"
        )
        await ctx.send(embed=embed)

    @config_command_group.command(name='feed', aliases=['-feed', '--feed', 'release', '-release', '--release', '-f', '-F'])
    @commands.guild_only()
    @commands.has_guild_permissions(manage_channels=True)
    @commands.bot_has_guild_permissions(manage_webhooks=True, manage_channels=True)
    @commands.cooldown(3, 30, commands.BucketType.guild)
    async def config_release_feed_command(self, ctx: commands.Context, repo: Optional[str] = None) -> None:
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
                        feed: list = [{'repo': repo.lower(), 'release': r['release']['tagName']}] if r and r[
                            'release'] else []
                    if hook:
                        await Mgr.db.guilds.insert_one(
                            {'_id': ctx.guild.id, 'hook': hook.url[33:], 'feed': feed if feed else []})
                        success_embed: discord.Embed = discord.Embed(
                            color=0x33ba7c,
                            title=ctx.l.config.feed.embeds.success.title,
                            description=ctx.fmt('embeds success description', channel.mention)
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
    @commands.cooldown(5, 30, commands.BucketType.user)
    async def config_user_command(self, ctx: commands.Context, user: str) -> None:
        u: bool = await Mgr.db.users.setitem(ctx, 'user', user)
        if u:
            await ctx.send(f"{Mgr.e.github}  {ctx.err(ctx.fmt('config qa_set user', user))}")
        else:
            await ctx.err(ctx.l.generic.nonexistent.user.base)

    @config_command_group.command(name='--org', aliases=['--organization', '-O', '-org', 'org'])
    @commands.cooldown(5, 30, commands.BucketType.user)
    async def config_org_command(self, ctx: commands.Context, org: str) -> None:
        o: bool = await Mgr.db.users.setitem(ctx, 'org', org)
        if o:
            await ctx.send(f"{Mgr.e.github}  {ctx.err(ctx.fmt('config qa_set org', org))}")
        else:
            await ctx.err(ctx.l.generic.nonexistent.org.base)

    @config_command_group.command(name='--repo', aliases=['--repository', '-R', '-repo', 'repo'])
    @commands.cooldown(5, 30, commands.BucketType.user)
    async def config_repo_command(self, ctx: commands.Context, repo: str) -> None:
        r: bool = await Mgr.db.users.setitem(ctx, 'repo', repo)
        if r:
            await ctx.send(f"{Mgr.e.github}  {ctx.err(ctx.fmt('config qa_set repo', repo))}")
        else:
            await ctx.err(ctx.l.generic.nonexistent.repo.base)

    @config_command_group.command(name='--lang', aliases=['-lang', 'lang', '--locale', '-locale', 'locale'])
    @commands.has_permissions(add_reactions=True)
    @commands.cooldown(5, 30, commands.BucketType.user)
    async def config_locale_command(self, ctx: commands.Context, locale: Optional[str] = None) -> None:
        ctx.fmt.set_prefix('config locale')
        if locale:
            l_ = Mgr.get_locale_meta_by_attribute(locale.lower())
            if l_:
                if not l_[1]:  # If it's not an exact match
                    match_confirmation_embed: discord.Embed = discord.Embed(
                        color=0xff009b,
                        title=f'{Mgr.e.github}  {ctx.l.config.locale.match_confirmation_embed.title}',
                        description=ctx.fmt('match_confirmation_embed description', l_[0]['localized_name'])
                    )
                    match_confirmation_embed.set_footer(text=ctx.l.config.locale.match_confirmation_embed.footer)
                    msg: discord.Message = await ctx.send(embed=match_confirmation_embed)
                    await msg.add_reaction(Mgr.e.checkmark)
                    await msg.add_reaction(Mgr.e.failure)
                    try:
                        def check(_reaction: discord.Reaction, _member: discord.Member) -> bool:
                            return all([_reaction.custom_emoji,
                                        _reaction.emoji.id in (770244076896256010, 770244084727283732),
                                        _member.id == ctx.author.id,
                                        _reaction.message.id == msg.id])
                        reaction: discord.Reaction
                        reaction, _ = await self.bot.wait_for('reaction_add',
                                                              timeout=30,
                                                              check=check)
                        await msg.delete()
                        if reaction.emoji.id == 770244076896256010:
                            await ctx.send(f'{Mgr.e.github}  {ctx.l.config.locale.cancelled}')
                            return
                    except asyncio.TimeoutError:
                        timeout_embed = discord.Embed(
                            color=0xffd500,
                            title=ctx.l.config.locale.timeout_embed.title
                        )
                        timeout_embed.set_footer(text=ctx.l.config.locale.timeout_embed.footer)
                        await msg.edit(embed=timeout_embed)
                        return
                await Mgr.db.users.setitem(ctx, 'locale', l_[0]['name'])
                setattr(ctx, 'l', await Mgr.get_locale(ctx))
                Mgr.locale_cache[ctx.author.id] = l_[0]['name']
                await ctx.send(f"{Mgr.e.github}  {ctx.fmt('success', l_[0]['localized_name'].capitalize())}")
                return
            else:
                await ctx.err(ctx.fmt('failure', locale), delete_after=3)

        def _format(locale_: dict):
            formatted: str = f'{Mgr.e.square} {locale_["flag"]} {locale_["localized_name"].capitalize()}'
            return formatted if ctx.l.meta.name != locale_['name'] else f'**{formatted}**'

        languages: list = [_format(l_) for l_ in Mgr.locale.languages]
        embed: discord.Embed = discord.Embed(
            color=0xefefef,
            title=f'{Mgr.e.github}  {ctx.l.config.locale.title}',
            description=f"{ctx.fmt('description', f'`git config --lang {{{ctx.l.argument_placeholders.lang}}}`')}\n" + '\n'.join(languages)
        )
        await ctx.send(embed=embed)

    @config_command_group.group(name='-delete', aliases=['-D', '-del', 'delete', '--delete'])
    @commands.cooldown(5, 30, commands.BucketType.user)
    async def delete_field_group(self, ctx: commands.Context) -> None:
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(
                color=0xefefef,
                title=f"{Mgr.e.github}  {ctx.l.config.delete.default.title}",
                description=f"{ctx.l.config.delete.default.description}\n"
                            f"`git config --delete user` {Mgr.e.arrow} {ctx.l.config.delete.default.commands.user}\n"
                            f"`git config --delete org` {Mgr.e.arrow} {ctx.l.config.delete.default.commands.org}\n"
                            f"`git config --delete repo` {Mgr.e.arrow} {ctx.l.config.delete.default.commands.repo}\n"
                            f"`git config --delete feed` {Mgr.e.arrow} {ctx.l.config.delete.default.commands.feed}\n"
                            f"`git config --delete all` {Mgr.e.arrow} {ctx.l.config.delete.default.commands.all}"
            )
            await ctx.send(embed=embed)

    @delete_field_group.group(name='feed', aliases=['-feed', '--feed'], invoke_without_command=True)
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True, manage_channels=True)
    @commands.cooldown(5, 30, commands.BucketType.guild)
    async def delete_feed_group(self, ctx: commands.Context, repo: Optional[str]) -> None:
        ctx.fmt.set_prefix('config delete feed default')
        if ctx.invoked_subcommand is None:
            if not repo:
                embed: discord.Embed = discord.Embed(
                    color=0xefefef,
                    title=ctx.l.config.delete.feed.default.title,
                    description=f'{ctx.l.config.delete.feed.default.description}\n'
                                f'`git config -delete feed {{{ctx.l.argument_placeholders.repo}}}` {Mgr.e.arrow} {ctx.l.config.delete.feed.default.commands.repo}\n'
                                f'`git config -delete feed all` {Mgr.e.arrow} {ctx.l.config.delete.feed.default.commands.all}\n'
                                f'`git config -delete feed total` {Mgr.e.arrow} {ctx.l.config.delete.feed.default.commands.total}'
                )
                await ctx.send(embed=embed)
            else:
                guild: Optional[dict] = await Mgr.db.guilds.find_one({'_id': ctx.guild.id})
                if guild:
                    for r in guild['feed']:
                        if r['repo'].lower() == repo.lower():
                            guild['feed'].remove(r)
                            await Mgr.db.guilds.update_one({'_id': ctx.guild.id}, {'$set': {'feed': guild['feed']}})
                            await ctx.send(f'{Mgr.e.github}  {ctx.l.config.delete.feed.repo.success.format(repo)}')
                            return
                    await ctx.err(ctx.l.config.delete.feed.repo.not_logged)
                else:
                    await ctx.err(ctx.l.config.delete.feed.no_channel)

    @delete_feed_group.command(name='all', aliases=['-all', '--all'])
    @commands.guild_only()
    @commands.cooldown(5, 30, commands.BucketType.guild)
    @commands.has_guild_permissions(manage_guild=True, manage_channels=True)
    async def delete_all_feeds_command(self, ctx: commands.Context) -> None:
        guild: Optional[dict] = await Mgr.db.guilds.find_one({'_id': ctx.guild.id})
        if guild is None:
            await ctx.err(ctx.l.config.delete.feed.nothing_deleted)
        else:
            if guild['feed']:
                await Mgr.db.guilds.update_one(guild, {'$set': {'feed': []}})
            await ctx.send(f'{Mgr.e.github}  {ctx.l.config.delete.feed.all.success}')

    @delete_feed_group.command(name='total', aliases=['-total', '--total', '-t'])
    @commands.guild_only()
    @commands.cooldown(5, 30, commands.BucketType.guild)
    @commands.has_guild_permissions(manage_guild=True, manage_channels=True)
    @commands.bot_has_guild_permissions()
    async def delete_feed_with_channel_command(self, ctx: commands.Context) -> None:
        guild: Optional[dict] = await Mgr.db.guilds.find_one({'_id': ctx.guild.id})
        if guild is None:
            await ctx.err(ctx.l.config.delete.feed.nothing_deleted)
        else:
            await Mgr.db.guilds.delete_one(guild)
            try:
                webhook: discord.Webhook = discord.Webhook.from_url('https://discord.com/api/webhooks/' + guild['hook'],
                                                                    adapter=discord.AsyncWebhookAdapter(Git.ses))
                await webhook.delete()
            except (discord.NotFound, discord.HTTPException):
                pass
            finally:
                await ctx.send(f'{Mgr.e.github}  {ctx.l.config.delete.feed.total.success}')

    @delete_field_group.command(name='user', aliases=['-U', '-user', '--user'])
    @commands.cooldown(5, 30, commands.BucketType.user)
    async def delete_user_command(self, ctx: commands.Context) -> None:
        deleted: bool = await Mgr.db.users.delitem(ctx, 'user')
        if deleted:
            await ctx.send(f"{Mgr.e.github}  {ctx.l.config.delete.user.success}")
        else:
            await ctx.err(ctx.l.config.delete.user.not_saved)

    @delete_field_group.command(name='org', aliases=['-O', '-org', 'organization', '-organization'])
    @commands.cooldown(5, 30, commands.BucketType.user)
    async def delete_org_command(self, ctx: commands.Context) -> None:
        deleted: bool = await Mgr.db.users.delitem(ctx, 'org')
        if deleted:
            await ctx.send(f"{Mgr.e.github}  {ctx.l.config.delete.org.success}")
        else:
            await ctx.err(ctx.l.config.delete.org.not_saved)

    @delete_field_group.command(name='repo', aliases=['-R', '-repo'])
    @commands.cooldown(5, 30, commands.BucketType.user)
    async def delete_repo_command(self, ctx: commands.Context) -> None:
        deleted: bool = await Mgr.db.users.delitem(ctx, 'repo')
        if deleted:
            await ctx.send(f"{Mgr.e.github}  {ctx.l.config.delete.repo.success}")
        else:
            await ctx.err(ctx.l.config.delete.repo.not_saved)

    @delete_field_group.command(name='all', aliases=['-A', '-all'])
    @commands.cooldown(5, 30, commands.BucketType.user)
    async def delete_entire_record_command(self, ctx: commands.Context) -> None:
        query: dict = await Mgr.db.users.find_one_and_delete({"_id": int(ctx.author.id)})
        if not query:
            await ctx.err(ctx.l.config.delete.all.not_saved)
            return
        await ctx.send(f"{Mgr.e.github}  {ctx.l.config.delete.all.success}")


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Config(bot))
