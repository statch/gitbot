from discord.ext import commands
from typing import Iterator, Optional
from lib.utils.decorators import gitbot_command, GitBotCommand, GitBotCommandGroup
from lib.utils import decorators
from lib.structs import GitBotEmbed
from lib.globs import Mgr
from lib.typehints import CommandHelp, CommandGroupHelp
from lib.structs.discord.context import GitBotContext


class Help(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot

    def _get_commands(self) -> Iterator[GitBotCommand | GitBotCommandGroup]:
        command: GitBotCommand | GitBotCommandGroup
        for command in self.bot.walk_commands():
            if not command.hidden:
                yield command

    def _get_command(self, name: str) -> Optional[GitBotCommand | GitBotCommandGroup]:
        if name.startswith(self.bot.command_prefix):
            name: str = name.strip(self.bot.command_prefix)
        return self.bot.get_command(name)

    def generate_command_help_embed(self,
                                    ctx: GitBotContext,
                                    command: GitBotCommand,
                                    content: Optional[CommandHelp | CommandGroupHelp] = None) -> GitBotEmbed:
        content: CommandHelp | CommandGroupHelp = content or command.get_help_content(ctx)
        embed: GitBotEmbed = GitBotEmbed(
            title=f'{Mgr.e.github}   {ctx.l.glossary.command}: `{command.fullname}`',
            description=f'```{content["brief"]}```',
            thumbnail=self.bot.user.avatar_url,
            url=f'https://docs.statch.tech'
        )
        if (example := content.get('example')) is not None:
            example: str = f'{self.bot.command_prefix}{example} ({ctx.l.glossary.example})'
        embed.add_field(name=f'{ctx.l.glossary.usage}:',
                        value=f'```haskell\n{self.bot.command_prefix}{content["usage"]}' +
                              (f'\n{Mgr.gen_separator_line(content["usage"], "-")}'
                               f'\n{example}```' if example else '```'))
        if content['description'] is not None:
            embed.add_field(name=f'{ctx.l.glossary.description}:',
                            value=f'```{content["description"]}```', inline=False)
        if argument_explainers := list(command.get_argument_explainers(ctx)):
            embed.add_field(name=f'{ctx.l.glossary.arguments}:',
                            value='\n'.join(f'**`{explainer["name"]}`**:'
                                            f'\n{explainer["content"]}' for explainer in argument_explainers),
                            inline=False)
        if permissions := list(command.get_permissions(ctx)):
            embed.add_field(name=f'{ctx.l.help.required_permissions}:',
                            value='\n'.join([f'{Mgr.e.circle_green}  {permission}' for permission
                                             in permissions]), inline=False)
        if qa_disclaimer := command.get_qa_disclaimer(ctx):
            embed.set_footer(text=qa_disclaimer)
        return embed

    async def send_command_help(self, ctx: GitBotContext, command: GitBotCommand) -> None:
        await ctx.send(embed=self.generate_command_help_embed(ctx, command))

    async def send_command_group_help(self, ctx: GitBotContext, command_group: GitBotCommandGroup) -> None:
        content: CommandGroupHelp = command_group.get_help_content(ctx)
        # since a group is basically a command with additional attributes, we can somewhat reuse the same embed
        embed: GitBotEmbed = self.generate_command_help_embed(ctx, command_group, content=content)
        embed.title = f'{Mgr.e.github}   {ctx.l.glossary.command_group}: `{command_group.fullname}`'
        embed.add_field(name=f'{ctx.l.help.commands_inside_group}:',
                        value='\n'.join([f':white_small_square: `{self.bot.command_prefix}{c}`'
                                         for c in content['commands']]), inline=False)
        await embed.send(ctx)

    @gitbot_command('help', aliases=['h', 'halp' 'commands', 'cmds',
                                     'cmd', 'cmdslist', 'cmdlist', 'cmds-list', 'cmd-list'])
    async def help_command(self, ctx: GitBotContext, *, command_or_group: Optional[str] = None) -> None:
        if command_or_group is not None:
            command_or_group: Optional[GitBotCommand | GitBotCommandGroup] = self._get_command(command_or_group)
            if not command_or_group:
                return await ctx.error(ctx.l.generic.nonexistent.command_or_group)
            match type(command_or_group):  # ah yes, the almighty type() call for checks. Don't kill me.
                case decorators.GitBotCommand:  # dot-access to resolve name capture pattern error - pep-0634
                    await self.send_command_help(ctx, command_or_group)
                case decorators.GitBotCommandGroup:
                    await self.send_command_group_help(ctx, command_or_group)
                case _:
                    pass  # TODO do something if a plain commands.command/group was used for some reason?


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Help(bot))
