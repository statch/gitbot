from discord.ext import commands
from discord import app_commands
from typing import Iterator, Optional
from lib.utils.decorators import gitbot_hybrid_command, GitBotCommand, GitBotCommandGroup
from lib.utils import decorators
from lib.structs import GitBotEmbed, GitBot, GitBotHybridCommand, GitBotHybridCommandGroup
from lib.structs.discord.pages import EmbedPages
from lib.typehints import CommandHelp, CommandGroupHelp
from lib.structs.discord.context import GitBotContext


class Help(commands.Cog):
    def __init__(self, bot: GitBot):
        self.bot: GitBot = bot

    def _get_commands(self) -> Iterator[GitBotCommand | GitBotCommandGroup]:
        command: GitBotCommand | GitBotCommandGroup
        for command in self.bot.walk_commands():
            if not command.hidden:
                yield command

    def _get_command(self, name: str) -> Optional[GitBotCommand | GitBotCommandGroup]:
        if (name := name.strip()).startswith(self.bot.command_prefix):
            name: str = name.strip(self.bot.command_prefix).strip()
        return self.bot.get_command(name)

    def generate_command_help_embed(self,
                                    ctx: GitBotContext,
                                    command: GitBotCommand | GitBotCommandGroup | GitBotHybridCommand | GitBotHybridCommandGroup,
                                    content: Optional[CommandHelp | CommandGroupHelp] = None) -> GitBotEmbed:
        content: CommandHelp | CommandGroupHelp = content or command.get_help_content(ctx)
        if not content:
            return GitBotEmbed.from_locale_resource(ctx, 'help no_help_for_command', color=self.bot.mgr.c.discord.white)
        embed: GitBotEmbed = GitBotEmbed(
            title=f'{self.bot.mgr.e.github}   {ctx.l.glossary.command}: `{command.fullname}`',
            description=f'```{content["brief"]}```',
            thumbnail=self.bot.user.avatar.url,
            url='https://docs.statch.org'
        )
        if (example := content.get('example')) is not None:
            example: str = f'{self.bot.command_prefix}{example} ({ctx.l.glossary.example})'
        embed.add_field(name=f'{ctx.l.glossary.usage}:',
                        value=f'```haskell\n{self.bot.command_prefix}{content["usage"]}' +
                              (f'\n{self.bot.mgr.gen_separator_line(content["usage"], "-")}'
                               f'\n{example}```' if example else '```'))
        if content['description'] is not None:
            embed.add_field(name=f'{ctx.l.glossary.description}:', value=f'```{content["description"]}```')
        if argument_explainers := list(command.get_argument_explainers(ctx)):
            embed.add_field(name=f'{ctx.l.glossary.arguments}:', value='\n'.join(f'**`{explainer["name"]}`**:'
                                                                                 f'\n{explainer["content"]}' for
                                                                                 explainer in argument_explainers))
        if permissions := list(command.get_permissions(ctx)):
            embed.add_field(name=f'{ctx.l.help.required_permissions}:',
                            value='\n'.join([f'{self.bot.mgr.e.circle_green}  {permission}' for permission
                                             in permissions]))
        if qa_disclaimer := command.get_qa_disclaimer(ctx):
            embed.set_footer(text=qa_disclaimer)
        if not argument_explainers:  # since there's no arguments, let's spice this embed up a bit
            embed.color = 0x268bd2
            embed.append_footer(text=f'{ctx.l.help.no_arguments_footer}', icon_url=self.bot.user.avatar.url)
        if isinstance(command, (GitBotHybridCommandGroup, GitBotHybridCommand)):
            embed.append_footer(text=ctx.l.help.hybrid_disclaimer)
        return embed

    async def send_command_help(self, ctx: GitBotContext, command: GitBotCommand) -> None:
        await ctx.send(embed=self.generate_command_help_embed(ctx, command))

    async def send_command_group_help(self, ctx: GitBotContext, command_group: GitBotCommandGroup) -> None:
        content: CommandGroupHelp = command_group.get_help_content(ctx)
        if not content:
            await GitBotEmbed.from_locale_resource(ctx, 'help no_help_for_command', color=self.bot.mgr.c.discord.white).send(ctx)
        else:
            # since a group is basically a command with additional attributes, we can somewhat reuse the same embed
            embed: GitBotEmbed = self.generate_command_help_embed(ctx, command_group, content=content)
            embed.title = f'{self.bot.mgr.e.github}   {ctx.l.glossary.command_group}: `{command_group.fullname}`'
            embed.add_field(name=f'{ctx.l.help.commands_inside_group}:',
                            value='\n'.join([f':white_small_square: `{self.bot.command_prefix}{c}`'
                                             for c in content['commands']]))
            await embed.send(ctx)

    async def send_help(self, ctx: GitBotContext) -> None:
        pages: EmbedPages = EmbedPages()
        index_embed: GitBotEmbed = GitBotEmbed.from_locale_resource(ctx, 'help default',
                                                                    url='https://docs.statch.org',
                                                                    color=self.bot.mgr.c.brand_colors.neon_bloom,
                                                                    thumbnail=self.bot.user.avatar.url)
        pages + index_embed
        chunks: list[list[GitBotCommand | GitBotCommandGroup]] = list(self.bot.mgr.chunks(list(self._get_commands()), 10))
        for chunk in chunks:
            embed: GitBotEmbed = GitBotEmbed(
                title=f'{self.bot.mgr.e.github}   Help',
                description='',
                url='https://docs.statch.org',
            )
            for command in chunk:
                try:
                    content: CommandHelp | CommandGroupHelp = command.get_help_content(ctx)
                    brief: str = self.bot.mgr.truncate(content['brief'], 70 - len(command.fullname), full_word=True)
                    embed.description += f'`{command.fullname}`: {brief}\n' if type(command) is GitBotCommand \
                        else f'`{command.fullname}`  {self.bot.mgr.e.folder}: {brief}\n'
                except (KeyError, TypeError) as e:
                    self.bot.dispatch('error', e)
            pages + embed
        await pages.start(ctx)

    @gitbot_hybrid_command('help', aliases=['h', 'halp' 'commands', 'cmds', 'cmd', 'cmdslist', 'cmdlist', 'cmds-list', 'cmd-list'], description='Get information about GitBot\'s commands.')
    @app_commands.rename(command_or_group='command')
    @app_commands.describe(
            command_or_group='The command you want to get help for. If omitted, the default help page will be shown.'
    )
    @commands.max_concurrency(2, commands.BucketType.user)
    async def help_command(self, ctx: GitBotContext, *, command_or_group: Optional[str] = None):
        if command_or_group is not None:
            command_or_group: Optional[GitBotCommand | GitBotCommandGroup] = self._get_command(command_or_group)
            if not command_or_group:
                return await ctx.error(ctx.l.generic.nonexistent.command_or_group)
            match type(command_or_group):  # ah yes, the almighty type() call for checks. Don't kill me.
                case decorators.GitBotCommand | decorators.GitBotHybridCommand:  # dot-access to avoid name capture pattern error - pep-0634
                    await self.send_command_help(ctx, command_or_group)
                case decorators.GitBotCommandGroup | decorators.GitBotHybridCommandGroup:
                    await self.send_command_group_help(ctx, command_or_group)
                case _:
                    ...
        else:
            await self.send_help(ctx)

    @help_command.autocomplete('command_or_group')
    async def help_autocomplete(self,
                                _,
                                current: str) -> list[app_commands.Choice[str]]:
        return [
            app_commands.Choice(name=str(cmd), value=str(cmd))
            for cmd in self._get_commands() if current.lower() in str(cmd).lower()
        ][:25]


async def setup(bot: GitBot) -> None:
    await bot.add_cog(Help(bot))
