from discord.ext import commands
from typing import Iterator, Optional
from lib.utils.decorators import gitbot_command, GitBotCommand
from lib.structs import GitBotEmbed
from lib.globs import Mgr
from lib.typehints import CommandHelp


class Help(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot

    def _get_commands(self) -> Iterator[GitBotCommand]:
        command: commands.Command
        for command in self.bot.walk_commands():
            if not command.hidden:
                yield command

    def _get_command(self, name: str) -> Optional[GitBotCommand]:
        if name.startswith(self.bot.command_prefix):
            name: str = name.strip(self.bot.command_prefix)
        return self.bot.get_command(name)

    async def send_command_help(self, ctx: commands.Context, command: GitBotCommand) -> None:
        content: CommandHelp = command.get_help_content(ctx)
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
                              f'\n{Mgr.gen_separator_line(content["usage"], "-")}'
                              f'\n{example}```' if example else '```')
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
