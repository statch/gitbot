import io
import json
import discord
from enum import Enum
from discord.ext import commands
from typing import Optional
from lib.structs import GitBotEmbed, GitBot
from lib.utils.decorators import gitbot_group, GitBotCommand, GitBotCommandGroup
from lib.structs.discord.context import GitBotContext


class ExportFileType(Enum):
    """
    Enum for the different export file types.
    """

    JSON = 'json'
    TEXT = 'txt'


class Dev(commands.Cog):
    def __init__(self, bot: GitBot):
        self.bot: GitBot = bot

    @gitbot_group('dev', hidden=True)
    @commands.cooldown(10, 60, commands.BucketType.user)
    async def dev_command_group(self, ctx: GitBotContext) -> None:
        ctx.fmt.set_prefix('dev default')
        if ctx.invoked_subcommand is None:
            commands_: list = [
                f'`git dev --missing-locales` - {ctx.l.dev.default.commands.missing_locales}'
            ]
            embed: GitBotEmbed = GitBotEmbed(
                color=0x0384fc,
                title=ctx.l.dev.default.title,
                url='https://github.com/statch/gitbot',
                description=(ctx.l.dev.default.description
                             + f'\n{"⎯" * (len(ctx.l.dev.default.title) * 2)}\n'
                             + '\n'.join(commands_)),
                footer=ctx.l.dev.default.footer
            )
            await ctx.send(embed=embed)

    @dev_command_group.command('missing-locales', hidden=True)
    @commands.cooldown(10, 60, commands.BucketType.user)
    async def missing_locales_command(self, ctx: GitBotContext, locale_: str) -> None:
        ctx.fmt.set_prefix('dev missing_locales')
        mk_data: Optional[tuple[list[str]], dict, bool] = self.bot.mgr.get_missing_keys_for_locale(locale_)
        if not mk_data:
            await ctx.error(ctx.l.generic.nonexistent.locale)
        elif not mk_data[0]:
            if mk_data[1]['name'] == self.bot.mgr.locale.master.meta.name:
                await ctx.error(ctx.fmt('no_master_locale', f'`{mk_data[1]["name"]}`'))
            else:
                await ctx.send(ctx.l.dev.missing_locales.no_missing_keys)
        elif len(mk_data[0]) < 80:
            def _gen_locale_path(steps) -> str:
                return ' **->** '.join([f'`{step}`' for step in steps])
            meta, _ = self.bot.mgr.get_locale_meta_by_attribute(locale_)
            missing: list[tuple[str]] = mk_data[0]
            embed: GitBotEmbed = GitBotEmbed(
                color=0x0384fc,
                title=ctx.fmt('title', meta['name']),
                url=f'https://github.com/statch/gitbot/blob/main/data/locale/{meta["name"]}.json',
                description='\n'.join([f'{self.bot.mgr.e.square} {_gen_locale_path(path)}' for path in missing])
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send(file=discord.File(fp=io.StringIO(json.dumps(mk_data[0], indent=2).encode('utf8')),
                                             filename=f'{locale_}_missing_keys.json'))

    @dev_command_group.command('export-commands', hidden=True)
    @commands.cooldown(1, 600, commands.BucketType.guild)
    async def export_commands_command(self, ctx: GitBotContext, format_: str = 'txt', direct: bool = False) -> None:
        try:
            format_: ExportFileType = ExportFileType(format_.lower())
        except ValueError:
            await ctx.error(ctx.fmt('invalid_format', ','.join([f'`{e.value}`' for e in ExportFileType])))
            return
        ctx.fmt.set_prefix('dev export_commands')
        command: GitBotCommand | GitBotCommandGroup
        commands_: list[str] = []
        for command in self.bot.walk_commands():
            if not command.hidden:
                commands_.append(command.fullname)
        match format_:
            case ExportFileType.TEXT:
                command_strings: str = '\n'.join(commands_)
            case ExportFileType.JSON:
                command_strings: str = json.dumps(commands_)
            case _:
                return
        if ctx.author.id == 548803750634979340 and not direct:
            f_name: str = f'commands.{format_.value}'
            s_dir: str = f'{self.bot.mgr.root_directory}/{f_name }'
            with open(s_dir, 'w+', encoding='utf8') as exportfile:
                exportfile.write(command_strings)
            await ctx.success(ctx.fmt('success_direct', f'`{f_name}`', len(commands_)))
            self.export_commands_command.reset_cooldown(ctx)
        else:
            await ctx.success(ctx.fmt('success_download', len(commands_)),
                              file=discord.File(fp=io.StringIO(command_strings),
                                                filename=f'commands.{format_.value}'))


async def setup(bot: GitBot) -> None:
    await bot.add_cog(Dev(bot))
