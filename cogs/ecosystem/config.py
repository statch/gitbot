import discord
import asyncio
from discord.ext import commands
from lib.globs import Git, Mgr
from lib.utils.decorators import normalize_repository, gitbot_group
from lib.typehints import (Repository, Organization,
                           GitHubUser, GitBotGuild,
                           ReleaseFeedItem, ReleaseFeed,
                           ReleaseFeedRepo, AutomaticConversion)
from typing import Optional, Literal


class Config(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot

    @gitbot_group('config', aliases=['cfg', 'configure'])
    @commands.cooldown(15, 30, commands.BucketType.user)
    async def config_command_group(self, ctx: commands.Context) -> None:
        if ctx.invoked_subcommand is None:
            lines: list = [ctx.l.config.default.brief_1,
                           "\n" + ctx.l.config.default.title,
                           ctx.l.config.default.brief_2,
                           f"`git config user {{{ctx.l.argument_placeholders.user}}}` " + Mgr.e.arrow + " " + ctx.l.config.default.commands.user,
                           f"`git config org {{{ctx.l.argument_placeholders.org}}}` " + Mgr.e.arrow + " " + ctx.l.config.default.commands.org,
                           f"`git config repo {{{ctx.l.argument_placeholders.repo}}}` " + Mgr.e.arrow + " " + ctx.l.config.default.commands.repo,
                           f"`git config language` " + Mgr.e.arrow + " " + ctx.l.config.default.commands.locale,
                           f"`git config feed` " + Mgr.e.arrow + " " + ctx.l.config.default.commands.feed,
                           "`git commits` " + Mgr.e.arrow + " " + ctx.l.help.utility.commands.commits,
                           "\n" + ctx.l.config.default.deletion]
            embed = discord.Embed(
                color=0xefefef,
                title=f"{Mgr.e.github}  {ctx.l.config.default.embed_title}",
                description='\n'.join(lines)
            )
            embed.set_footer(text=ctx.l.config.default.footer)
            await ctx.send(embed=embed)

    def construct_release_feed_list(self, ctx: commands.Context, rf: ReleaseFeed) -> str:
        item: str = '' if rf else ctx.l.generic.nonexistent.release_feed
        for rfi in rf:
            item += Mgr.e.square + ' ' + f'<#{rfi["cid"]}>\n' + \
                    ('\n'.join([f'⠀⠀- `{rfr["name"]}`' for rfr in rfi['repos']]) if rfi['repos']
                     else f'⠀⠀- {ctx.l.config.show_feed.no_repos}') + '\n'
        return item

    @config_command_group.command(name='show', aliases=['s'])
    @commands.cooldown(5, 30, commands.BucketType.user)
    async def config_show_command(self, ctx: commands.Context) -> None:
        ctx.fmt.set_prefix('config show')
        query: dict = await Mgr.db.users.find_one({'_id': ctx.author.id}) or {}
        guild: Optional[dict] = None
        if not isinstance(ctx.channel, discord.DMChannel):
            guild: Optional[dict] = await Mgr.db.guilds.find_one({'_id': ctx.guild.id})
        if not query and guild is None or ((guild and len(guild) == 1) and not query):
            await ctx.err(ctx.l.generic.nonexistent.qa)
            return
        lang: str = ctx.fmt('accessibility list locale', f'`{ctx.l.meta.localized_name.capitalize()}`')
        user: str = ctx.fmt('qa list user', f'`{query["user"]}`' if 'user' in query else f'`{ctx.l.config.show.item_not_set}`')
        org: str = ctx.fmt('qa list org', f'`{query["org"]}`' if 'org' in query else f'`{ctx.l.config.show.item_not_set}`')
        repo: str = ctx.fmt('qa list repo', f'`{query["repo"]}`' if 'repo' in query else f'`{ctx.l.config.show.item_not_set}`')
        accessibility: list = ctx.l.config.show.accessibility.heading + '\n' + '\n'.join([lang])
        qa: list = ctx.l.config.show.qa.heading + '\n' + '\n'.join([user, org, repo])
        guild_str: str = ''
        if not isinstance(ctx.channel, discord.DMChannel):
            feed: str = ctx.l.config.show.guild.list.feed + '\n' + '\n'.join([f'{Mgr.e.square} <#{rfi["cid"]}>'
                                                                              for rfi in guild['feed']]) \
                if (guild and guild.get('feed')) else f'{ctx.l.config.show.guild.list.feed}' \
                                                      f' `{ctx.l.config.show.item_not_configured}`'
            guild_str: str = ctx.l.config.show.guild.heading + '\n' + '\n'.join([feed])
        shortest_heading_len: int = min(map(len, [ctx.l.config.show.accessibility.heading,
                                                  ctx.l.config.show.guild.heading,
                                                  ctx.l.config.show.qa.heading]))
        linebreak: str = f'\n{"⎯" * shortest_heading_len}\n'
        embed = discord.Embed(
            color=Mgr.c.discord.blurple,
            title=f"{Mgr.e.github}  {ctx.l.config.show.title}",
            description=f"{accessibility}{linebreak}{qa}{linebreak if guild_str else ''}{guild_str}"
        )
        embed.set_footer(text=ctx.fmt('footer', 'git config show-feed'))
        await ctx.send(embed=embed)

    @config_command_group.command(name='show-feed', aliases=['sf'])
    @commands.guild_only()
    @commands.cooldown(5, 30, commands.BucketType.user)
    async def config_show_feed_command(self, ctx: commands.Context):
        ctx.fmt.set_prefix('config show_feed')
        guild: Optional[dict] = await Mgr.db.guilds.find_one({'_id': ctx.guild.id})
        if guild and 'feed' in guild:
            embed = discord.Embed(
                color=Mgr.c.discord.blurple,
                title=f"{Mgr.e.github}  {ctx.l.config.show_feed.title}",
                description=self.construct_release_feed_list(ctx, guild['feed'])
            )
            embed.set_footer(text=ctx.fmt('footer', f'git config feed channel {{{ctx.l.argument_placeholders.channel}}}'))
            await ctx.send(embed=embed)
        else:
            await ctx.err(ctx.l.generic.nonexistent.release_feed)

    @config_command_group.group(name='feed', aliases=['release', 'f', 'releases'], invoke_without_command=True)
    @commands.cooldown(7, 30, commands.BucketType.guild)
    async def config_release_feed_group(self, ctx: commands.Context) -> None:
        if ctx.invoked_subcommand is None:
            ctx.fmt.set_prefix('config feed default')
            embed: discord.Embed = discord.Embed(
                color=Mgr.c.discord.fuchsia,
                title=ctx.l.config.feed.default.title,
                description=ctx.fmt('description',
                                    f'`git config feed channel {{{ctx.l.argument_placeholders.channel}}}`',
                                    f'`git config feed repo {{{ctx.l.argument_placeholders.repo}}}`')
            )
            await ctx.send(embed=embed)

    async def create_webhook(self, ctx: commands.Context, channel: discord.TextChannel) -> Optional[discord.Webhook]:
        try:
            return await channel.create_webhook(name=self.bot.user.name,
                                                reason=f'Release Feed channel setup by {ctx.author}')
        except discord.errors.Forbidden:
            await ctx.err(ctx.l.config.feed.channel.no_perms)

    @config_release_feed_group.command('channel')
    @commands.has_guild_permissions(manage_channels=True)
    @commands.bot_has_guild_permissions(manage_webhooks=True, manage_channels=True)
    @commands.cooldown(5, 30, commands.BucketType.guild)
    async def feed_channel_command(self, ctx: commands.Context, channel) -> None:
        ctx.fmt.set_prefix('config feed channel')
        try:
            channel: Optional[discord.TextChannel] = await commands.TextChannelConverter().convert(ctx, channel)
        except commands.BadArgument:
            await ctx.err(ctx.l.config.feed.channel.invalid_channel)
            return
        g: dict = await Mgr.db.guilds.find_one({'_id': ctx.guild.id})
        success: bool = False
        if g:
            if len(g['feed']) >= 5:
                embed_limit_reached: discord.Embed = discord.Embed(
                    color=Mgr.c.discord.yellow,
                    title=ctx.l.config.feed.channel.embeds.channel_limit_reached_embed.title,
                    description=ctx.l.config.feed.embeds.channel.channel_limit_reached_embed.description
                )
                embed_limit_reached.set_footer(text=ctx.l.config.feed.channel.embeds.channel_limit_reached_embed.footer,
                                               icon_url=self.bot.user.avatar_url)
                await ctx.send(embed=embed_limit_reached)
                return
            for rfi in g['feed']:
                if rfi['cid'] == channel.id:
                    await ctx.err(ctx.l.config.feed.channel.already_taken)
                    return
            hook: discord.Webhook = await self.create_webhook(ctx, channel)
            if hook:
                await Mgr.db.guilds.update_one(g, {'$push': {'feed': ReleaseFeed(cid=channel.id,
                                                                                 hook=hook.url[33:],
                                                                                 repos=[])}})
                success: bool = True
        else:
            hook: discord.Webhook = await self.create_webhook(ctx, channel)
            if hook:
                await Mgr.db.guilds.insert_one(GitBotGuild(_id=ctx.guild.id, feed=[ReleaseFeed(cid=channel.id,
                                                                                               hook=hook.url[33:],
                                                                                               repos=[])]))
                success: bool = True
        if success:
            embed: discord.Embed = discord.Embed(
                color=Mgr.c.discord.green,
                title=ctx.l.config.feed.channel.success_embed.title,
                description=ctx.fmt(f'success_embed description',
                                    channel.mention,
                                    f'`git config feed repo {{{ctx.l.argument_placeholders.repo}}}`')
            )
            embed.set_footer(text=ctx.fmt('success_embed footer',
                                          'git config delete feed channel'))
            await ctx.send(embed=embed)

    @config_release_feed_group.command('repo', aliases=['repository'])
    @commands.has_guild_permissions(manage_channels=True)
    @commands.bot_has_guild_permissions(manage_webhooks=True, manage_channels=True)
    @commands.cooldown(5, 30, commands.BucketType.guild)
    @normalize_repository
    async def feed_repo_command(self, ctx: commands.Context, repo: Repository) -> None:
        ctx.fmt.set_prefix('config feed repo')
        release: Optional[dict] = await Git.get_latest_release(repo)
        if not release:
            await ctx.err(ctx.l.generic.nonexistent.repo.base)
            return
        tag: Optional[str] = (release.get('release') or {'tagName': None}).get('tagName')
        guild: GitBotGuild = await Mgr.db.guilds.find_one({'_id': ctx.guild.id})
        if not guild or not guild.get('feed'):
            await ctx.err(ctx.l.generic.nonexistent.release_feed)
            return
        channel_list_embed_description: str = '\n'.join([f'{Mgr.e.square}**{index + 1} | **<#{rfi["cid"]}>'
                                                         for index, rfi in enumerate(guild['feed'])])
        channel_list_embed: discord.Embed = discord.Embed(
            color=Mgr.c.cyan,
            title=ctx.l.config.feed.repo.channel_list_embed.title,
            description=channel_list_embed_description
        )
        channel_list_embed.set_footer(text=ctx.l.config.feed.repo.channel_list_embed.footer)
        channel_list_message: discord.Message = await ctx.send(embed=channel_list_embed)
        while True:
            try:
                indexes: list[dict] = [dict(number=ind+1, rfi=rfi) for ind, rfi in enumerate(guild['feed'])]
                msg: discord.Message = await self.bot.wait_for('message',
                                                               check=lambda msg_: (msg_.channel.id == ctx.channel.id
                                                                                   and msg_.author.id == ctx.author.id),
                                                               timeout=30)
                if msg.content.lower() == 'cancel':
                    await msg.delete()
                    await ctx.err(ctx.l.config.feed.repo.cancelled)
                    return
                await ctx.trigger_typing()

                async def _try_convert() -> Optional[dict]:
                    try:
                        channel: discord.TextChannel = await commands.TextChannelConverter().convert(ctx, msg.content)
                        return Mgr.get_by_key_from_sequence(indexes, 'rfi cid', channel.id)
                    except commands.BadArgument:
                        return

                if selected_index := (await Mgr.validate_index(msg.content, indexes) or await _try_convert()):
                    selected_rfi: ReleaseFeedItem = selected_index['rfi']
                    mention: str = f'<#{selected_rfi["cid"]}>'
                    if len(selected_rfi['repos']) < 10:
                        if (repo := repo.lower()) not in map(lambda r: r['name'], selected_rfi['repos']):
                            await Mgr.db.guilds.update_one(guild,
                                                           {'$push':
                                                            {f'feed.{guild["feed"].index(selected_rfi)}.repos':
                                                             ReleaseFeedRepo(name=repo.lower(), tag=tag)}})
                            await ctx.success(ctx.fmt('success',
                                                      f'`{repo}`',
                                                      mention))
                        else:
                            await ctx.err(ctx.fmt('already_logged', f'`{repo}`', mention))
                    else:
                        channel_at_limit_embed: discord.Embed = discord.Embed(
                            color=Mgr.c.discord.yellow,
                            title=ctx.l.config.feed.repo.channel_at_limit_embed.title,
                            description=ctx.fmt('channel_at_limit_embed description',
                                                mention,
                                                f'`{repo}`'))
                        channel_at_limit_embed.set_footer(text=ctx.fmt('channel_at_limit_embed footer',
                                                                       'git config delete feed repo'))
                        await ctx.send(embed=channel_at_limit_embed)
                    return
                else:
                    await ctx.err(ctx.fmt('invalid_channel', msg.content))
                    continue
            except asyncio.TimeoutError:
                timeout_embed: discord.Embed = discord.Embed(
                    color=Mgr.c.discord.yellow,
                    title=ctx.l.config.feed.repo.timeout_embed.title,
                )
                timeout_embed.set_footer(text=ctx.l.config.feed.repo.timeout_embed.footer)
                await channel_list_message.edit(embed=timeout_embed)

    @config_command_group.command(name='user', aliases=['u'])
    @commands.cooldown(5, 30, commands.BucketType.user)
    async def config_user_command(self, ctx: commands.Context, user: GitHubUser) -> None:
        u: bool = await Mgr.db.users.setitem(ctx, 'user', user)
        if u:
            await ctx.success(ctx.fmt('config qa_set user', user))
        else:
            await ctx.err(ctx.l.generic.nonexistent.user.base)

    @config_command_group.command(name='org', aliases=['organization', 'o'])
    @commands.cooldown(5, 30, commands.BucketType.user)
    async def config_org_command(self, ctx: commands.Context, org: Organization) -> None:
        o: bool = await Mgr.db.users.setitem(ctx, 'org', org)
        if o:
            await ctx.success(ctx.fmt('config qa_set org', org))
        else:
            await ctx.err(ctx.l.generic.nonexistent.org.base)

    @config_command_group.command(name='repo', aliases=['repository', 'r'])
    @commands.cooldown(5, 30, commands.BucketType.user)
    @normalize_repository
    async def config_repo_command(self, ctx: commands.Context, repo: Repository) -> None:
        r: bool = await Mgr.db.users.setitem(ctx, 'repo', repo)
        if r:
            await ctx.success(ctx.fmt('config qa_set repo', repo))
        else:
            await ctx.err(ctx.l.generic.nonexistent.repo.base)

    @config_command_group.command(name='lang', aliases=['locale', 'language'])
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
                await ctx.success(ctx.fmt('success', l_[0]['localized_name'].capitalize()))
                return
            await ctx.err(ctx.fmt('failure', locale), delete_after=7)

        def _format(locale_: dict):
            formatted: str = f'{Mgr.e.square} {locale_["flag"]} {locale_["localized_name"].capitalize()}'
            return formatted if ctx.l.meta.name != locale_['name'] else f'**{formatted}**'

        languages: list = [_format(l_) for l_ in Mgr.locale.languages]
        embed: discord.Embed = discord.Embed(
            color=0xefefef,
            title=f'{Mgr.e.github}  {ctx.l.config.locale.title}',
            description=f"{ctx.fmt('description', f'`git config --lang {{{ctx.l.argument_placeholders.lang}}}`')}\n⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n" + '\n'.join(languages)
        )
        await ctx.send(embed=embed)

    @config_command_group.group('autoconv',
                                aliases=['automatic-conversion', 'auto-conversion'],
                                invoke_without_command=True)
    @commands.guild_only()
    @commands.cooldown(5, 30, commands.BucketType.guild)
    async def config_autoconv_group(self, ctx: commands.Context) -> None:
        pass

    async def do_carbon_toggle(self, ctx: commands.Context, type_: Literal['codeblock', 'link']) -> None:
        config: AutomaticConversion
        config, did_exist = await Mgr.get_autoconv_config(ctx, True)
        _other_type = 'link' if type_ != 'link' else 'codeblock'
        carbon_config[type_] = (state := not carbon_config[type_])
        if did_exist:
            await Mgr.db.guilds.update_one({'_id': ctx.guild.id}, {'$set': {'carbon': carbon_config}})
        else:
            await Mgr.db.guilds.insert_one(GitBotGuild(_id=ctx.guild.id,
                                                       carbon=carbon_config,
                                                       feed=[]))
        Mgr.autoconv_cache[ctx.guild.id] = carbon_config
        await ctx.success(ctx.l.config.carbon[type_][str(state).lower()])

    @config_autoconv_group.group('link', aliases=['lines'])
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True, manage_channels=True)
    @commands.cooldown(5, 30, commands.BucketType.guild)
    async def config_autoconv_toggle_link_command(self, ctx: commands.Context, mode: Optional[str] = None) -> None:
        await self.do_carbon_toggle(ctx, 'link')

    @config_autoconv_group.command('codeblock', aliases=['code'])
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True, manage_channels=True)
    @commands.cooldown(5, 30, commands.BucketType.guild)
    async def config_autoconv_toggle_carbon_codeblock_command(self, ctx: commands.Context) -> None:
        await self.do_carbon_toggle(ctx, 'codeblock')

    @config_command_group.group(name='delete', aliases=['d', 'del'])
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

    @delete_field_group.group(name='feed', invoke_without_command=True)
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True, manage_channels=True)
    @commands.cooldown(5, 30, commands.BucketType.guild)
    @normalize_repository
    async def delete_feed_group(self, ctx: commands.Context) -> None:
        ctx.fmt.set_prefix('config delete feed default')
        if ctx.invoked_subcommand is None:
            pass

    @delete_feed_group.command('channel')
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True, manage_channels=True)
    @commands.cooldown(5, 30, commands.BucketType.guild)
    async def delete_feed_channel_command(self, ctx: commands.Context, channel: str):
        embed: discord.Embed = discord.Embed(

        )

    @delete_feed_group.command('repo')
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True, manage_channels=True)
    @commands.cooldown(5, 30, commands.BucketType.guild)
    async def delete_feed_repo_command(self, ctx: commands.Context, repo: Repository):
        pass

    @delete_field_group.command(name='user', aliases=['u'])
    @commands.cooldown(5, 30, commands.BucketType.user)
    async def delete_user_command(self, ctx: commands.Context) -> None:
        deleted: bool = await Mgr.db.users.delitem(ctx, 'user')
        if deleted:
            await ctx.success(ctx.l.config.delete.user.success)
        else:
            await ctx.err(ctx.l.config.delete.user.not_saved)

    @delete_field_group.command(name='org', aliases=['o', 'organization'])
    @commands.cooldown(5, 30, commands.BucketType.user)
    async def delete_org_command(self, ctx: commands.Context) -> None:
        deleted: bool = await Mgr.db.users.delitem(ctx, 'org')
        if deleted:
            await ctx.success(ctx.l.config.delete.org.success)
        else:
            await ctx.err(ctx.l.config.delete.org.not_saved)

    @delete_field_group.command(name='repo', aliases=['r'])
    @commands.cooldown(5, 30, commands.BucketType.user)
    async def delete_repo_command(self, ctx: commands.Context) -> None:
        deleted: bool = await Mgr.db.users.delitem(ctx, 'repo')
        if deleted:
            await ctx.success(ctx.l.config.delete.repo.success)
        else:
            await ctx.err(ctx.l.config.delete.repo.not_saved)

    @delete_field_group.command(name='language', aliases=['lang', 'locale'])
    @commands.cooldown(5, 30, commands.BucketType.user)
    async def delete_locale_command(self, ctx: commands.Context) -> None:
        await Mgr.db.users.delitem(ctx, 'locale')
        await ctx.success(ctx.l.config.delete.locale)

    @delete_field_group.command(name='all', aliases=['a'])
    @commands.cooldown(5, 30, commands.BucketType.user)
    async def delete_entire_record_command(self, ctx: commands.Context) -> None:
        query: dict = await Mgr.db.users.find_one_and_delete({'_id': ctx.author.id})
        if not query:
            await ctx.err(ctx.l.config.delete.all.not_saved)
            return
        await ctx.success(ctx.l.config.delete.all.success)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Config(bot))
