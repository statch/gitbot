from discord.ext import commands
from typing import Iterator, Optional
from lib.utils.decorators import gitbot_command, GitBotCommand
from lib.structs import GitBotEmbed
from lib.globs import Mgr
from lib.typehints import CommandHelp


class Help(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot

    def _normalize_command_name(self, command: GitBotCommand) -> str:
        name: str = self._command_name(command)
        return name.lower().replace(' ', '_')

    def _get_commands(self) -> Iterator[GitBotCommand]:
        command: commands.Command
        for command in self.bot.walk_commands():
            if not command.hidden:
                yield command

    def _get_command(self, name: str) -> Optional[GitBotCommand]:
        if name.startswith(self.bot.command_prefix):
            name: str = name.strip(self.bot.command_prefix)
        return self.bot.get_command(name)

    def _command_name(self, command: GitBotCommand) -> str:
        return command.name if not command.full_parent_name else f'{command.full_parent_name} {command.name}'

    def _get_argument_explainers(self, ctx: commands.Context, command: GitBotCommand) -> Iterator[dict[str, str]]:
        for explainer in command.argument_explainers:
            yield ctx.l.help.argument_explainers[explainer]

    def _get_qa_disclaimer(self, ctx: commands.Context, command: GitBotCommand) -> str:
        return ctx.l.help.qa_disclaimers[command.qa_resource]

    def _get_permissions(self, ctx: commands.Context, command: GitBotCommand) -> str:
        for permission_resource_name in command.required_permissions:
            yield ctx.l.permissions[permission_resource_name]

    def _get_localized_command_help_content(self, ctx: commands.Context, command: GitBotCommand) -> CommandHelp:
        l_cmd: dict[str, str] = ctx.l.help.commands[self._normalize_command_name(command)]
        l_cmd['usage'] = l_cmd.get('usage', self._command_name(command))
        return l_cmd

    async def send_command_help(self, ctx: commands.Context, command: GitBotCommand) -> None:
        content: CommandHelp = self._get_localized_command_help_content(ctx, command)
        embed: GitBotEmbed = GitBotEmbed(
            title=f'{Mgr.e.github}   {ctx.l.glossary.command}: `{self._command_name(command)}`',
            description=f'```{content["brief"]}```',
            thumbnail=self.bot.user.avatar_url,
            url=f'https://docs.statch.tech'
        )

        argument_explainers: list[dict[str, str]] = list(self._get_argument_explainers(ctx, command))
        permissions: list[str] = list(self._get_permissions(ctx, command))
        if example := content.get('example'):
            example: str = f'{self.bot.command_prefix}{example} ({ctx.l.glossary.example})'
        embed.add_field(name=f'{ctx.l.glossary.usage}:',
                        value=f'```haskell\n{self.bot.command_prefix}{content["usage"]}' +
                              f'\n{Mgr.gen_separator_line(content["usage"], "-")}'
                              f'\n{example}```' if example else '```')
        if description := content.get('description'):
            embed.add_field(name=f'{ctx.l.glossary.description}:',
                            value=f'```{description}```', inline=False)
        if argument_explainers:
            embed.add_field(name=f'{ctx.l.glossary.arguments}:',
                            value='\n'.join(f'**`{explainer["name"]}`**:'
                                            f'\n{explainer["content"]}' for explainer in argument_explainers),
                            inline=False)
        if permissions:
            embed.add_field(name=f'{ctx.l.help.required_permissions}:',
                            value='\n'.join([f'{Mgr.e.circle_green}  {permission}' for permission
                                             in permissions]), inline=False)
        if qa_disclaimer := self._get_qa_disclaimer(ctx, command):
            embed.set_footer(text=qa_disclaimer)
        await embed.send(ctx)

    @gitbot_command('help', aliases=["h", "halp", "commands", "cmds", "cmd", "cmdslist", "cmdlist", "cmds-list", "cmd-list"])
    async def help_command(self, ctx: commands.Context, *, command: Optional[str] = None) -> None:
        if command is not None:
            command: Optional[GitBotCommand] = self._get_command(command)
            if not command or not isinstance(command, GitBotCommand):
                return await ctx.err(ctx.l.generic.nonexistent.command)
            await self.send_command_help(ctx, command)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Help(bot))
