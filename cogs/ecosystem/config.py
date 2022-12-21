from lib.utils.decorators import *
from lib.typehints import (GitHubRepository, GitHubOrganization,
                           GitHubUser, GitBotGuild,
                           ReleaseFeedItem, ReleaseFeed,
                           ReleaseFeedRepo, AutomaticConversionSettings,
                           GitBotUser)
from typing import Optional, Literal, Any
from lib.structs import GitBotEmbed, GitBotCommandState, GitBot
from lib.utils.regex import DISCORD_CHANNEL_MENTION_RE
from lib.utils.decorators import normalize_repository
from lib.structs.discord.context import GitBotContext


class Config(commands.Cog):
    def __init__(self, bot: GitBot):
        self.bot: GitBot = bot
        self.lines_state_map: dict = {
            ('none', 'no', 'off', 'disable', 'disabled'): 0,
            ('raw', 'text', 'codeblock', 'block', 'plaintext', 'txt'): 1,
            ('carbon', 'image', 'carbonara', 'img'): 2
        }

    @staticmethod
    def construct_release_feed_list(ctx: GitBotContext, rf: ReleaseFeed) -> str:
        item: str = '' if rf else ctx.l.generic.nonexistent.release_feed
        for rfi in rf:
            m: str = '' if not rfi.get('mention') else ' - ' + ctx.bot.mgr.release_feed_mention_to_actual(rfi['mention'])
            item += ctx.bot.mgr.e.square + ' ' + f'<#{rfi["cid"]}>{m}\n' + \
                    ('\n'.join([f'⠀⠀- [`{rfr["name"]}`](https://github.com/{rfr["name"]})'
                                for rfr in rfi['repos']]) if rfi['repos']
                     else f'⠀⠀- {ctx.l.config.show.feed.no_repos}') + '\n'
        return item

    @staticmethod
    async def toggle_autoconv_item(ctx: GitBotContext,
                                   item: Literal['gh_url', 'codeblock']) -> bool:
        guild: GitBotGuild = await ctx.bot.mgr.db.guilds.find_one({'_id': ctx.guild.id}) or {}
        config: AutomaticConversionSettings = guild.get('autoconv', ctx.bot.mgr.env.autoconv_default)
        config[item] = (state := not (config.get(item, ctx.bot.mgr.env.autoconv_default[item])))  # noqa item is str
        if guild:
            await ctx.bot.mgr.db.guilds.update_one({'_id': guild['_id']}, {'$set': {f'autoconv.{item}': state}})
        else:
            await ctx.bot.mgr.db.guilds.insert_one(GitBotGuild(_id=ctx.guild.id, autoconv=config))  # noqa _id is int
        ctx.bot.mgr.autoconv_cache[ctx.guild.id] = config
        await ctx.success(ctx.l.config.autoconv.toggles.get(item).get(str(state)))
        return state

    @staticmethod
    async def get_feed_prerequisites(ctx: GitBotContext) -> tuple[GitBotGuild, ReleaseFeed]:
        guild: GitBotGuild = await ctx.bot.mgr.db.guilds.find_one({'_id': ctx.guild.id}) or {}
        feed: ReleaseFeed = guild.get('feed', [])
        return guild, feed

    @gitbot_group('config', aliases=['cfg', 'configure', 'settings'])
    @commands.cooldown(15, 30, commands.BucketType.user)
    async def config_command_group(self, ctx: GitBotContext) -> None:
        await ctx.group_help()

    @config_command_group.group(name='show', aliases=['s'])
    @commands.cooldown(5, 30, commands.BucketType.user)
    async def config_show_command_group(self, ctx: GitBotContext) -> None:
        if ctx.invoked_subcommand is None:
            ctx.fmt.set_prefix('config show base')
            user: GitBotUser = await self.bot.mgr.db.users.find_one({'_id': ctx.author.id}) or {}
            guild: Optional[GitBotGuild] = None
            if not isinstance(ctx.channel, discord.DMChannel):
                guild: Optional[GitBotGuild] = await self.bot.mgr.db.guilds.find_one({'_id': ctx.guild.id})
            if not user and guild is None or ((guild and len(guild) == 1) and not user):
                await ctx.error(ctx.l.generic.nonexistent.qa)
                return
            lang: str = ctx.fmt('accessibility list locale', f'`{ctx.l.meta.localized_name.capitalize()}`')
            user_str, org, repo = (ctx.fmt(f'qa list {item}', f'[`{item}`](https://github.com/{item})' if item in user else
                                           f'`{ctx.l.config.show.base.item_not_set}`') for item in ('user', 'org', 'repo'))
            accessibility: list = ctx.l.config.show.base.accessibility.heading + '\n' + '\n'.join([lang])
            qa: list = ctx.l.config.show.base.qa.heading + '\n' + '\n'.join([user_str, org, repo])
            guild_str: str = ''
            if not isinstance(ctx.channel, discord.DMChannel):
                feed: str = ctx.l.config.show.base.guild.list.feed + '\n' + '\n'.join([f'{self.bot.mgr.e.square} <#{rfi["cid"]}>'
                                                                                       for rfi in guild['feed']]) \
                    if (guild and guild.get('feed')) else f'{ctx.l.config.show.base.guild.list.feed}' \
                                                          f' `{ctx.l.config.show.base.item_not_configured}`'
                ctx.fmt.set_prefix('+guild list autoconv')
                if not guild:
                    ac: AutomaticConversionSettings = self.bot.mgr.env.autoconv_default
                else:
                    ac: AutomaticConversionSettings = {k: (v if k not in (_ac := guild.get('autoconv', {}))
                                                       else _ac[k]) for k, v in self.bot.mgr.env.autoconv_default.items()}
                codeblock: str = ctx.fmt('codeblock',
                                         f'`{ctx.l.enum.generic.switch[str(ac["codeblock"])]}`')
                lines: str = ctx.fmt('gh_lines',
                                     f'`{ctx.l.enum.autoconv.gh_lines[str(ac["gh_lines"])]}`')
                url: str = ctx.fmt('gh_url', f'`{ctx.l.enum.generic.switch[str(ac["gh_url"])]}`')
                autoconv: str = (ctx.l.config.show.base.guild.list.autoconv.heading + '\n'
                                 + '\n'.join([f'{self.bot.mgr.e.square} {aci}' for aci in [codeblock, url, lines]]))
                guild_str: str = ctx.l.config.show.base.guild.heading + '\n' + '\n'.join([autoconv, feed])
            shortest_heading_len: int = min(map(len, [ctx.l.config.show.base.accessibility.heading,
                                                      ctx.l.config.show.base.guild.heading,
                                                      ctx.l.config.show.base.qa.heading]))
            linebreak: str = f'\n{self.bot.mgr.gen_separator_line(shortest_heading_len)}\n'
            embed = discord.Embed(
                color=self.bot.mgr.c.discord.blurple,
                title=f"{self.bot.mgr.e.github}  {ctx.l.config.show.base.title}",
                description=f"{accessibility}{linebreak}{qa}{linebreak if guild_str else ''}{guild_str}"
            )
            if guild:
                embed.set_footer(text=ctx.fmt('!config show base footer', 'git config show feed'))
            await ctx.send(embed=embed)

    @config_show_command_group.command(name='feed', aliases=['release', 'f', 'releases'])
    @commands.guild_only()
    @commands.cooldown(5, 30, commands.BucketType.user)
    async def config_show_feed_command(self, ctx: GitBotContext):
        ctx.fmt.set_prefix('config show feed')
        guild: Optional[dict] = await self.bot.mgr.db.guilds.find_one({'_id': ctx.guild.id})
        if guild and 'feed' in guild:
            embed: GitBotEmbed = GitBotEmbed(
                color=self.bot.mgr.c.discord.blurple,
                title=f"{self.bot.mgr.e.github}  {ctx.l.config.show.feed.title}",
                description=self.construct_release_feed_list(ctx, guild['feed']),
                footer=ctx.fmt('footer', f'git config feed channel {{{ctx.l.help.argument_explainers.channel.name}}}'))
            await embed.send(ctx)
        else:
            await ctx.error(ctx.l.generic.nonexistent.release_feed)

    @config_command_group.group(name='feed', aliases=['release', 'f', 'releases'], invoke_without_command=True)
    @commands.cooldown(7, 30, commands.BucketType.guild)
    async def config_release_feed_group(self, ctx: GitBotContext) -> None:
        await ctx.group_help()

    async def create_webhook(self, ctx: GitBotContext, channel: discord.TextChannel) -> Optional[discord.Webhook]:
        try:
            return await channel.create_webhook(name=self.bot.user.name, reason=f'Release Feed channel setup by {ctx.author}')
        except discord.errors.Forbidden:
            await ctx.error(ctx.l.config.feed.no_perms)

    @config_release_feed_group.command('channel')
    @commands.has_guild_permissions(manage_channels=True)
    @bot_can_manage_release_feed_channels()
    @commands.bot_has_guild_permissions(manage_webhooks=True)
    @commands.cooldown(5, 30, commands.BucketType.guild)
    async def feed_channel_command(self, ctx: GitBotContext, channel) -> None:
        ctx.fmt.set_prefix('config feed channel')
        try:
            channel: Optional[discord.TextChannel] = await commands.TextChannelConverter().convert(ctx, channel)
        except commands.BadArgument:
            await ctx.error(ctx.l.config.feed.channel.invalid_channel)
            return
        guild: Optional[GitBotGuild] = await self.bot.mgr.db.guilds.find_one({'_id': ctx.guild.id})
        success: bool = False
        if guild:
            feed: dict = guild.get('feed', {})
            if len(feed) >= 5:
                embed_limit_reached: discord.Embed = discord.Embed(
                    color=self.bot.mgr.c.discord.yellow,
                    title=ctx.l.config.feed.channel.embeds.channel_limit_reached_embed.title,
                    description=ctx.l.config.feed.embeds.channel.channel_limit_reached_embed.description
                )
                embed_limit_reached.set_footer(text=ctx.l.config.feed.channel.embeds.channel_limit_reached_embed.footer,
                                               icon_url=self.bot.user.avatar.url)
                await ctx.send(embed=embed_limit_reached)
                return
            for rfi in feed:
                if rfi['cid'] == channel.id:
                    await ctx.error(ctx.l.config.feed.channel.already_taken)
                    return
            hook: discord.Webhook = await self.create_webhook(ctx, channel)
            if hook:
                await self.bot.mgr.db.guilds.update_one(guild, {'$push': {'feed': ReleaseFeedItem(cid=channel.id,
                                                                                                  hook=hook.url[33:],
                                                                                                  repos=[])}})
                success: bool = True
        else:
            hook: discord.Webhook = await self.create_webhook(ctx, channel)
            if hook:
                await self.bot.mgr.db.guilds.insert_one(GitBotGuild(_id=ctx.guild.id, feed=[ReleaseFeedItem(cid=channel.id,
                                                                                                            hook=hook.url[33:],
                                                                                                            repos=[])]))
                success: bool = True
        if success:
            embed: GitBotEmbed = GitBotEmbed(
                color=self.bot.mgr.c.discord.green,
                title=ctx.l.config.feed.channel.success_embed.title,
                description=ctx.fmt('success_embed description',
                                    channel.mention,
                                    f'`git config feed repo {{{ctx.l.help.argument_explainers.repo.name}}}`'),
                footer=ctx.fmt('success_embed footer', 'git config delete feed channel')
            )
            await ctx.send(embed=embed)

    @config_release_feed_group.command('repo', aliases=['repository'])
    @commands.has_guild_permissions(manage_channels=True)
    @bot_can_manage_release_feed_channels()
    @guild_has_release_feeds()
    @commands.bot_has_guild_permissions(manage_webhooks=True)
    @commands.cooldown(5, 30, commands.BucketType.guild)
    @normalize_repository
    async def feed_repo_command(self, ctx: GitBotContext, repo: GitHubRepository) -> None:
        ctx.fmt.set_prefix('config feed repo')
        release: Optional[dict] = await self.bot.github.get_latest_release(repo)
        if not release:
            await ctx.error(ctx.l.generic.nonexistent.repo.base)
            return
        tag: Optional[str] = (release.get('release') or {'tagName': None}).get('tagName')
        guild: GitBotGuild = await self.bot.mgr.db.guilds.find_one({'_id': ctx.guild.id})
        if not guild or not guild.get('feed'):
            await ctx.error(ctx.l.generic.nonexistent.release_feed)
            return
        channel_list_embed_description: str = '\n'.join([f'{self.bot.mgr.e.square}**{index + 1} | **<#{rfi["cid"]}>'
                                                         for index, rfi in enumerate(guild['feed'])])
        channel_list_embed: GitBotEmbed = GitBotEmbed(
            color=self.bot.mgr.c.cyan,
            title=ctx.l.config.feed.repo.channel_list_embed.title,
            description=channel_list_embed_description,
            footer=ctx.l.config.feed.repo.channel_list_embed.footer
        )

        async def _callback(_, res: discord.Message, repo_: str):
            indexes: list[dict] = [dict(number=ind + 1, rfi=rfi) for ind, rfi in enumerate(guild['feed'])]
            if res.content.lower() in ('quit', 'cancel'):
                await ctx.error(ctx.l.config.feed.repo.cancelled)
                return GitBotCommandState.FAILURE
            await ctx.typing()

            async def _try_convert() -> Optional[dict]:
                try:
                    channel: discord.TextChannel = await commands.TextChannelConverter().convert(ctx, res.content)
                    return self.bot.mgr.get_by_key_from_sequence(indexes, 'rfi cid', channel.id)
                except commands.BadArgument:
                    return

            if selected_index := (await self.bot.mgr.validate_index(res.content, indexes) or await _try_convert()):
                selected_rfi: ReleaseFeedItem = selected_index['rfi']
                mention: str = f'<#{selected_rfi["cid"]}>'
                if len(selected_rfi['repos']) < 10:
                    if (repo_ := repo_.lower()) not in map(lambda r: r['name'], selected_rfi['repos']):
                        await self.bot.mgr.db.guilds.update_one(guild,
                                                                {'$push':
                                                                 {f'feed.{guild["feed"].index(selected_rfi)}.repos':
                                                                  ReleaseFeedRepo(name=repo_.lower(), tag=tag)}})
                        await ctx.success(ctx.fmt('success',
                                                  f'`{repo_}`',
                                                  mention))
                        return GitBotCommandState.SUCCESS
                    else:
                        await ctx.error(ctx.fmt('already_logged', f'`{repo_}`', mention))
                else:
                    channel_at_limit_embed: discord.Embed = discord.Embed(
                        color=self.bot.mgr.c.discord.yellow,
                        title=ctx.l.config.feed.repo.channel_at_limit_embed.title,
                        description=ctx.fmt('channel_at_limit_embed description',
                                            mention,
                                            f'`{repo_}`'))
                    channel_at_limit_embed.set_footer(text=ctx.fmt('channel_at_limit_embed footer',
                                                                   'git config delete feed repo'))
                    await ctx.send(embed=channel_at_limit_embed)
                return GitBotCommandState.FAILURE
            else:
                await ctx.error(ctx.fmt('invalid_channel', res.content))
                return GitBotCommandState.CONTINUE

        await channel_list_embed.input_with_timeout(
            ctx=ctx,
            event='message',
            timeout=30,
            timeout_check=lambda msg: msg.channel.id == ctx.channel.id and msg.author.id == ctx.author.id,
            response_callback=_callback,
            repo_=repo
        )

    @config_release_feed_group.command('mention', aliases=['ping'])
    @commands.has_guild_permissions(manage_channels=True)
    @bot_can_manage_release_feed_channels()
    @commands.bot_has_guild_permissions(manage_webhooks=True)
    @commands.cooldown(5, 30, commands.BucketType.guild)
    async def config_release_feed_mention(self, ctx: GitBotContext, channel: discord.TextChannel):
        ctx.fmt.set_prefix('config feed mention')
        guild, feed = await self.get_feed_prerequisites(ctx)
        if not feed:
            await ctx.error(ctx.l.generic.nonexistent.release_feed)
            return

        rfi: ReleaseFeedItem = self.bot.mgr.get_by_key_from_sequence(feed, 'cid', channel.id)
        if not rfi:
            return await ctx.error(ctx.fmt('!config feed not_a_feed', channel.mention))

        mention_ask_embed: GitBotEmbed = GitBotEmbed(
            color=self.bot.mgr.c.cyan,
            title=ctx.fmt('embed title', f'`#{channel.name}`'),
            description=ctx.l.config.feed.mention.embed.description,
            footer=ctx.l.config.feed.mention.embed.footer
        )

        async def _callback(_, res: discord.Message):
            if res.content.lower() in ('quit', 'cancel'):
                await ctx.error(ctx.fmt('cancelled', channel.mention))
                return GitBotCommandState.FAILURE
            elif (rfi_mention_enum := res.content.lower().strip('@')) in ('everyone', 'here'):
                return GitBotCommandState.SUCCESS, rfi_mention_enum
            elif res.role_mentions or res.content.isnumeric() and len(res.content) == 18:
                if not res.role_mentions:
                    try:
                        res.role_mentions[0] = await commands.RoleConverter().convert(ctx, res.content)
                    except commands.BadArgument:
                        await ctx.error(ctx.l.config.feed.mention.invalid)
                        return GitBotCommandState.CONTINUE
                return GitBotCommandState.SUCCESS, res.role_mentions[0].id
            else:
                await ctx.error(ctx.l.config.feed.mention.invalid)
                return GitBotCommandState.CONTINUE

        id_or_enum: int | str | None
        _, id_or_enum = await mention_ask_embed.input_with_timeout(
            ctx=ctx,
            event='message',
            timeout=45,
            timeout_check=lambda msg: msg.channel.id == ctx.channel.id and msg.author.id == ctx.author.id,
            response_callback=_callback,
        )
        if not id_or_enum:
            return

        await ctx.success(ctx.fmt('success', channel.mention, self.bot.mgr.release_feed_mention_to_actual(id_or_enum)),
                          allowed_mentions=discord.AllowedMentions.none())
        await self.bot.mgr.db.guilds.update_one(guild, {'$set': {f'feed.{guild["feed"].index(rfi)}.mention': id_or_enum}})

    @config_command_group.command(name='user', aliases=['u'])
    @commands.cooldown(5, 30, commands.BucketType.user)
    async def config_user_command(self, ctx: GitBotContext, user: GitHubUser) -> None:
        u: bool = await self.bot.mgr.db.users.setitem(ctx, 'user', user)
        if u:
            await ctx.success_embed(ctx.fmt('config qa_set user', self.bot.mgr.to_github_hyperlink(user, True)))
        else:
            await ctx.error(ctx.l.generic.nonexistent.user.base)

    @config_command_group.command(name='org', aliases=['organization', 'o'])
    @commands.cooldown(5, 30, commands.BucketType.user)
    async def config_org_command(self, ctx: GitBotContext, org: GitHubOrganization) -> None:
        o: bool = await self.bot.mgr.db.users.setitem(ctx, 'org', org)
        if o:
            await ctx.success_embed(ctx.fmt('config qa_set org', self.bot.mgr.to_github_hyperlink(org, True)))
        else:
            await ctx.error(ctx.l.generic.nonexistent.org.base)

    @config_command_group.command(name='repo', aliases=['repository', 'r'])
    @commands.cooldown(5, 30, commands.BucketType.user)
    @normalize_repository
    async def config_repo_command(self, ctx: GitBotContext, repo: GitHubRepository) -> None:
        r: bool = await self.bot.mgr.db.users.setitem(ctx, 'repo', repo)
        if r:
            await ctx.success_embed(ctx.fmt('config qa_set repo', self.bot.mgr.to_github_hyperlink(repo, True)))
        else:
            await ctx.error(ctx.l.generic.nonexistent.repo.base)

    @config_command_group.command(name='lang', aliases=['locale', 'language'])
    @commands.bot_has_guild_permissions(add_reactions=True)
    @commands.cooldown(5, 30, commands.BucketType.user)
    async def config_locale_command(self, ctx: GitBotContext, locale: Optional[str] = None) -> None:
        ctx.fmt.set_prefix('config locale')
        if locale:
            l_ = self.bot.mgr.get_locale_meta_by_attribute(locale.lower())
            if l_:
                if not l_[1]:  # If it's not an exact match
                    async def _callback(_, event):
                        if event[0].emoji.id == 770244076896256010:
                            await ctx.info(ctx.l.config.locale.cancelled)
                            return GitBotCommandState.FAILURE
                        return GitBotCommandState.SUCCESS

                    _match_confirmation_embed: GitBotEmbed = GitBotEmbed(
                        color=0xff009b,
                        title=f'{self.bot.mgr.e.github}  {ctx.l.config.locale.match_confirmation_embed.title}',
                        description=ctx.fmt('match_confirmation_embed description', l_[0]['localized_name']),
                        footer=ctx.l.config.locale.match_confirmation_embed.footer
                    )
                    confirmation_result: bool = await _match_confirmation_embed.confirmation(ctx, _callback)
                    if not confirmation_result:
                        return
                await self.bot.mgr.db.users.setitem(ctx, 'locale', l_[0]['name'])
                setattr(ctx, 'l', await self.bot.mgr.get_locale(ctx))
                self.bot.mgr.locale_cache[ctx.author.id] = l_[0]['name']
                await ctx.success_embed(ctx.fmt('success', l_[0]['localized_name'].capitalize()))
                return
            await ctx.error(ctx.fmt('failure', locale), delete_after=7)

        def _format(locale_: dict):
            formatted: str = f'{self.bot.mgr.e.square} {locale_["flag"]} {locale_["localized_name"].capitalize()} ([{locale_["author"]["name"]}]({locale_["author"]["url"]}))'
            return formatted if ctx.l.meta.name != locale_['name'] else f'**{formatted}**'

        languages: list = [_format(l_) for l_ in self.bot.mgr.locale.languages]
        embed: discord.Embed = discord.Embed(
            color=self.bot.mgr.c.rounded,
            title=f'{self.bot.mgr.e.github}  {ctx.l.config.locale.title}',
            description=f"{ctx.fmt('description', f'`git config lang {{{ctx.l.help.argument_explainers.locale.name}}}`')}\n⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n" + '\n'.join(
                languages)
        )
        await ctx.send(embed=embed)

    @config_command_group.group('autoconv',
                                aliases=['automatic-conversion', 'auto-conversion', 'auto'],
                                invoke_without_command=True)
    @commands.guild_only()
    @commands.cooldown(5, 30, commands.BucketType.guild)
    async def config_autoconv_group(self, ctx: GitBotContext) -> None:
        await ctx.group_help()

    @config_autoconv_group.command('codeblock')
    @commands.guild_only()
    @commands.cooldown(5, 30, commands.BucketType.guild)
    @commands.has_guild_permissions(manage_channels=True)
    async def config_autoconv_codeblock_command(self, ctx: GitBotContext) -> None:
        await self.toggle_autoconv_item(ctx, 'codeblock')

    @config_autoconv_group.command('link', aliases=['links', 'url', 'urls'])
    @commands.guild_only()
    @commands.cooldown(5, 30, commands.BucketType.guild)
    @commands.has_guild_permissions(manage_channels=True)
    async def config_autoconv_gh_url_command(self, ctx: GitBotContext) -> None:
        await self.toggle_autoconv_item(ctx, 'gh_url')

    def _validate_github_lines_conversion_state(self, state: str | int) -> Optional[int]:
        if state is not None:
            _int_state: Optional[int] = state if isinstance(state, int) else (int(state) if state.isnumeric() else None)
            if _int_state is not None:
                if _int_state != 0:
                    _int_state -= 1
                if _int_state in self.lines_state_map.values():
                    return _int_state
            for k, v in self.lines_state_map.items():
                if state.lower() in k:
                    return v

    @config_autoconv_group.command('lines', aliases=['line', 'githublines', 'github-lines', 'gh-lines'])
    @commands.guild_only()
    @commands.cooldown(5, 30, commands.BucketType.guild)
    @commands.has_guild_permissions(manage_channels=True)
    async def config_autoconv_lines_command(self, ctx: GitBotContext, skip_state: Optional[str] = None) -> None:
        ctx.fmt.set_prefix('config autoconv gh_lines')
        skip_state: Optional[int] = self._validate_github_lines_conversion_state(skip_state)
        guild: Optional[GitBotGuild] = await self.bot.mgr.db.guilds.find_one({'_id': ctx.guild.id})
        if skip_state is None:
            embed: GitBotEmbed = GitBotEmbed(
                color=self.bot.mgr.c.rounded,
                title=ctx.lp.embed.title,
                description=(ctx.lp.embed.description
                             + '\n' + self.bot.mgr.gen_separator_line(len(ctx.lp.embed.title))
                             + '\n' + self.bot.mgr.option_display_list_format(ctx.lp.embed.options)),
                footer=ctx.lp.embed.footer
            )

            async def _callback(_, res: discord.Message):
                if res.content.lower() in ('quit', 'cancel'):
                    await ctx.error(ctx.lp.cancelled)
                    return GitBotCommandState.FAILURE, None
                elif (state := self._validate_github_lines_conversion_state(res.content)) is not None:
                    return GitBotCommandState.SUCCESS, state
                await ctx.send(ctx.lp.invalid_response)
                return GitBotCommandState.CONTINUE, None

            response, actual_state = await embed.input_with_timeout(
                ctx=ctx,
                event='message',
                timeout=30,
                timeout_check=lambda m: m.channel.id == ctx.channel.id and m.author.id == ctx.author.id,
                response_callback=_callback,
            )
            if not response:
                return
        else:
            actual_state = skip_state
        if (_str := str(actual_state)) in ctx.lp.results.keys():
            if guild:
                config: AutomaticConversionSettings = guild.get('autoconv', self.bot.mgr.env.autoconv_default)
                config['gh_lines'] = actual_state
                await self.bot.mgr.db.guilds.update_one({'_id': guild['_id']}, {'$set': {'autoconv.gh_lines': actual_state}})
            else:
                config: AutomaticConversionSettings = self.bot.mgr.env.autoconv_default
                config['gh_lines'] = actual_state
                await self.bot.mgr.db.guilds.insert_one({'_id': ctx.guild.id, 'autoconv': config})
            self.bot.mgr.autoconv_cache[ctx.guild.id] = config
            await ctx.success(ctx.lp.results[_str])

    @config_command_group.group(name='delete', aliases=['d', 'del'])
    @commands.cooldown(5, 30, commands.BucketType.user)
    async def delete_field_group(self, ctx: GitBotContext) -> None:
        ctx.fmt.set_prefix('config delete default')
        if not ctx.invoked_subcommand:
            embed: GitBotEmbed = GitBotEmbed(
                color=self.bot.mgr.c.rounded,
                title=f"{self.bot.mgr.e.github}  {ctx.lp.title}",
                description=f"{ctx.lp.description}\n"
                            f"`git config --delete user` {self.bot.mgr.e.arrow} {ctx.lp.commands.user}\n"
                            f"`git config --delete org` {self.bot.mgr.e.arrow} {ctx.lp.commands.org}\n"
                            f"`git config --delete repo` {self.bot.mgr.e.arrow} {ctx.lp.commands.repo}\n"
                            f"`git config --delete feed` {self.bot.mgr.e.arrow} {ctx.lp.commands.feed}\n"
                            f"`git config --delete all` {self.bot.mgr.e.arrow} {ctx.lp.commands.all}"
            )
            await ctx.send(embed=embed)

    delete_feed_group: commands.Group

    @delete_field_group.group(name='feed', invoke_without_command=True)
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True, manage_channels=True)
    @commands.cooldown(5, 30, commands.BucketType.guild)
    async def delete_feed_group(self, ctx: GitBotContext) -> None:
        await ctx.group_help()

    @delete_feed_group.command('channel')
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True, manage_channels=True)
    @commands.cooldown(5, 30, commands.BucketType.guild)
    async def delete_feed_channel_command(self, ctx: GitBotContext, channel: discord.TextChannel) -> None:
        ctx.fmt.set_prefix('config delete feed channel')
        _, feed = await self.get_feed_prerequisites(ctx)
        if not feed:
            await ctx.error(ctx.l.generic.nonexistent.release_feed)
            return
        rfi: ReleaseFeedItem = self.bot.mgr.get_by_key_from_sequence(feed, 'cid', channel.id)
        if not rfi:
            await ctx.error(ctx.fmt('not_a_feed', channel.mention))
            return
        ctx.fmt.set_prefix('+flow confirmation')
        embed: GitBotEmbed = GitBotEmbed(
            color=self.bot.mgr.c.cyan,
            title=ctx.l.config.delete.feed.channel.explicit.confirmation.embed.title,
            description=ctx.fmt('embed description', channel.mention, f'`{len(rfi["repos"])}`'),
            footer=ctx.l.config.delete.feed.channel.explicit.confirmation.embed.footer
        )

        async def _callback(_, event):
            if event[0].emoji.id == 770244076896256010:
                await ctx.info(ctx.fmt('cancelled', channel.mention))
                return GitBotCommandState.FAILURE
            return GitBotCommandState.SUCCESS

        if await embed.confirmation(ctx, _callback):
            await self.bot.mgr.db.guilds.update_one({'_id': ctx.guild.id}, {'$pull': {'feed': rfi}})
            await ctx.success(ctx.fmt('success', channel.mention))

    def parse_channel_mention_or_number_response(self,
                                                 msg: discord.Message,
                                                 rfis: list[ReleaseFeedItem]) -> list[int]:
        numbers: list[int] = self.bot.mgr.get_numbers_in_range_in_str(msg.content, len(rfis))
        channel_ids: list[int] = [int(g) for g in DISCORD_CHANNEL_MENTION_RE.findall(msg.content)]
        for n in numbers:
            channel_ids.append(rfis[n - 1]['cid'])
        return channel_ids

    @delete_feed_group.command('repo')
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True, manage_channels=True)
    @commands.cooldown(5, 30, commands.BucketType.guild)
    @normalize_repository
    async def delete_feed_repo_command(self, ctx: GitBotContext, repo: GitHubRepository):
        ctx.fmt.set_prefix('config delete feed repo')
        guild, feed = await self.get_feed_prerequisites(ctx)
        if not guild or not feed:
            return await ctx.error(ctx.l.generic.nonexistent.release_feed)
        present_in: list[ReleaseFeedItem] = []
        for rfi in feed:
            if repo in [rfr['name'].lower() for rfr in rfi['repos']]:
                present_in.append(rfi)
        if not present_in:
            return await ctx.error(ctx.l.config.delete.feed.repo.not_present_in_feed)
        elif (_len := len(present_in)) > 1:
            ctx.fmt.set_prefix('+multiple')
            options: str = self.bot.mgr.option_display_list_format([f'<#{rfi["cid"]}>' for rfi in present_in])
            embed: GitBotEmbed = GitBotEmbed(
                color=self.bot.mgr.c.cyan,
                title=ctx.fmt('embed title', f'`{repo.lower()}`'),
                url=f'https://github.com/{repo.lower()}',
                description=(ctx.fmt('embed description', f'`{repo}`')
                             + '\n' + self.bot.mgr.gen_separator_line(20) + '\n'
                             + options),
                footer=ctx.l.config.delete.feed.repo.multiple.embed.footer
            )

            async def _callback(_, res: discord.Message) -> tuple[GitBotCommandState, None] | tuple[
                GitBotCommandState, list[int]] | tuple[GitBotCommandState, list[Any]]:
                if res.content.lower() in ('quit', 'cancel'):
                    await ctx.error(ctx.l.config.delete.feed.repo.multiple.cancelled)
                    return GitBotCommandState.FAILURE, None
                found: list[int] = self.parse_channel_mention_or_number_response(res, present_in)
                if found:
                    return GitBotCommandState.SUCCESS, found
                await ctx.error(ctx.l.config.delete.feed.repo.multiple.no_feeds_mentioned)
                return GitBotCommandState.CONTINUE, []

            _, to_delete = await embed.input_with_timeout(
                ctx=ctx,
                event='message',
                timeout=30,
                timeout_check=lambda m: m.author.id == ctx.author.id and m.channel.id == ctx.channel.id,
                response_callback=_callback,
            )

            if to_delete:
                ctx.fmt.set_prefix('+success')
                to_delete: list = self.bot.mgr.get_by_key_from_sequence(present_in, 'cid', to_delete, multiple=True, unpack=True)
                ud: dict = {f'feed.{guild["feed"].index(to_delete[n])}.repos':
                            self.bot.mgr.get_by_key_from_sequence(rf['repos'],
                                                         'name', repo.lower()) for n, rf in enumerate(to_delete)}
                await self.bot.mgr.db.guilds.update_one({'_id': ctx.guild.id}, {'$pull': ud})
                result_embed: GitBotEmbed = GitBotEmbed(
                    color=self.bot.mgr.c.discord.green,
                    title=ctx.l.config.delete.feed.repo.multiple.success.title,
                    description=(ctx.fmt('description', self.bot.mgr.to_github_hyperlink(repo.lower(), codeblock=True)) + '\n' +
                                 '\n'.join(f'{self.bot.mgr.e.square} <#{rfi_["cid"]}>' for rfi_ in to_delete))
                )
                if len(present_in) != len(to_delete):
                    result_embed.set_footer(text=ctx.fmt('optional_footer', len(to_delete)))
                await result_embed.send(ctx)
        else:
            ctx.fmt.set_prefix('+single')
            embed: GitBotEmbed = GitBotEmbed(
                color=self.bot.mgr.c.cyan,
                title=ctx.fmt('embed title', f'`{repo.lower()}`'),
                description=ctx.fmt('embed description',
                                    self.bot.mgr.to_github_hyperlink(repo, codeblock=True),
                                    f'<#{present_in[0]["cid"]}>')
            )

            async def _callback(_, event):
                if event[0].emoji.id == 770244076896256010:
                    await ctx.info(ctx.fmt('cancelled', f'`{repo}`'))
                    return GitBotCommandState.FAILURE
                return GitBotCommandState.SUCCESS
            delete: bool = await embed.confirmation(ctx, _callback)
            if delete:
                rfr: ReleaseFeedRepo = self.bot.mgr.get_by_key_from_sequence(present_in[0]['repos'], 'name', repo.lower())
                await self.bot.mgr.db.guilds.update_one({'_id': ctx.guild.id},
                                               {'$pull': {f'feed.{guild["feed"].index(present_in[0])}.repos': rfr}})
                await ctx.success(ctx.fmt('success', f'`{repo.lower()}`', f'<#{present_in[0]["cid"]}>'))

    @delete_feed_group.command(name='mention')
    @commands.guild_only()
    @commands.has_guild_permissions(manage_channels=True)
    @commands.cooldown(5, 60, commands.BucketType.guild)
    async def delete_feed_mention_command(self, ctx: GitBotContext):
        ctx.fmt.set_prefix('config delete feed mention')
        guild, feed = await self.get_feed_prerequisites(ctx)
        if not guild or not feed:
            return await ctx.error(ctx.l.generic.nonexistent.release_feed)
        rfis_with_mention: list = [rfi for rfi in feed if rfi.get('mention')]
        if not rfis_with_mention:
            return await ctx.error(ctx.l.generic.nonexistent.release_feed_with_mention)
        selection_embed: GitBotEmbed = GitBotEmbed(
                color=self.bot.mgr.c.cyan,
                title=ctx.lp.embed.title,
                description=(ctx.lp.embed.description
                             + f'\n{self.bot.mgr.gen_separator_line(20)}\n'
                             + self.bot.mgr.option_display_list_format([f'<#{rfi["cid"]}> - '
                                                                       f'{self.bot.mgr.release_feed_mention_to_actual(rfi["mention"])}'
                                                                        for rfi in rfis_with_mention])),
                footer=ctx.lp.embed.footer
        )

        async def _callback(_, res: discord.Message) -> tuple[GitBotCommandState, None] | tuple[
            GitBotCommandState, int]:
            if res.content.lower() in ('quit', 'cancel'):
                await ctx.error(ctx.lp.cancelled)
                return GitBotCommandState.FAILURE, None
            found: list[int] = self.parse_channel_mention_or_number_response(res, rfis_with_mention)
            if found:
                return GitBotCommandState.SUCCESS, found[0]
            await ctx.error(ctx.lp.invalid)
            return GitBotCommandState.CONTINUE, None

        _, to_delete = await selection_embed.input_with_timeout(
                ctx=ctx,
                event='message',
                timeout=30,
                timeout_check=lambda m: m.author.id == ctx.author.id and m.channel.id == ctx.channel.id,
                response_callback=_callback
        )

        if to_delete:
            to_delete: ReleaseFeedItem = self.bot.mgr.get_by_key_from_sequence(feed, 'cid', to_delete)
            await self.bot.mgr.db.guilds.update_one({'_id': guild['_id']},
                                           {'$set': {f'feed.{feed.index(to_delete)}.mention': None}})
            await ctx.success(ctx.fmt('success',
                                      self.bot.mgr.release_feed_mention_to_actual(to_delete['mention']),
                                      f'<#{to_delete["cid"]}>'), allowed_mentions=discord.AllowedMentions.none())

    @delete_field_group.command(name='user', aliases=['u'])
    @commands.cooldown(5, 30, commands.BucketType.user)
    async def delete_user_command(self, ctx: GitBotContext) -> None:
        deleted: bool = await self.bot.mgr.db.users.delitem(ctx, 'user')
        if deleted:
            await ctx.success(ctx.l.config.delete.user.success)
        else:
            await ctx.error(ctx.l.config.delete.user.not_saved)

    @delete_field_group.command(name='org', aliases=['o', 'organization'])
    @commands.cooldown(5, 30, commands.BucketType.user)
    async def delete_org_command(self, ctx: GitBotContext) -> None:
        deleted: bool = await self.bot.mgr.db.users.delitem(ctx, 'org')
        if deleted:
            await ctx.success(ctx.l.config.delete.org.success)
        else:
            await ctx.error(ctx.l.config.delete.org.not_saved)

    @delete_field_group.command(name='repo', aliases=['r'])
    @commands.cooldown(5, 30, commands.BucketType.user)
    async def delete_repo_command(self, ctx: GitBotContext) -> None:
        deleted: bool = await self.bot.mgr.db.users.delitem(ctx, 'repo')
        if deleted:
            await ctx.success(ctx.l.config.delete.repo.success)
        else:
            await ctx.error(ctx.l.config.delete.repo.not_saved)

    @delete_field_group.command(name='language', aliases=['lang', 'locale'])
    @commands.cooldown(5, 30, commands.BucketType.user)
    async def delete_locale_command(self, ctx: GitBotContext) -> None:
        await self.bot.mgr.db.users.delitem(ctx, 'locale')
        await ctx.success(ctx.l.config.delete.locale)

    @delete_field_group.command(name='all', aliases=['a'])
    @commands.cooldown(5, 30, commands.BucketType.user)
    async def delete_entire_record_command(self, ctx: GitBotContext) -> None:
        # This command's naming is confusing to users.
        # It should either be removed or reworked to better reflect its effect on users' config values
        query: dict = await self.bot.mgr.db.users.find_one_and_delete({'_id': ctx.author.id})
        if not query:
            await ctx.error(ctx.l.config.delete.all.not_saved)
            return
        await ctx.success(ctx.l.config.delete.all.success)


async def setup(bot: GitBot) -> None:
    await bot.add_cog(Config(bot))
