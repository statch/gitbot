# coding: utf-8

"""
GitBot - the developer toolkit for Discord
~~~~~~~~~~~~~~~~~~~
A developer toolkit for the Discord era, with a focus on sleek design and powerful features.
:copyright: (c) 2020-present statch
:license: CC BY-NC-ND 4.0, see LICENSE for more details.
"""

import discord
from os import getenv
from dotenv import load_dotenv
from discord.ext import commands
from lib.structs.discord.context import GitBotContext
from lib.structs.discord.bot import GitBot

# all of the configuration is handled inside the class, there is no real need to pass anything here
bot = GitBot()


async def do_cog_op(ctx: GitBotContext, cog: str, op: str) -> None:
    if (cog := cog.lower()) == 'all':
        done: int = 0
        try:
            for ext in bot.extensions:
                getattr(bot, f'{op}_extension')(str(ext))
                done += 1
        except commands.ExtensionError as e:
            await ctx.error(f'**Exception during batch-{op}ing:**\n```{e}```')
        else:
            await ctx.success(f'All extensions **successfully {op}ed.** ({done})')
    else:
        try:
            getattr(bot, f'{op}_extension')(cog)
        except commands.ExtensionError as e:
            await ctx.error(f'**Exception while {op}ing** `{cog}`**:**\n```{e}```')
        else:
            await ctx.success(f'**Successfully {op}ed** `{cog}`.')


@bot.command(name='reload', hidden=True)
@commands.is_owner()
async def reload_command(ctx: GitBotContext, cog: str) -> None:
    await do_cog_op(ctx, cog, 'reload')


@bot.command(name='load', hidden=True)
@commands.is_owner()
async def load_command(ctx: GitBotContext, cog: str) -> None:
    await do_cog_op(ctx, cog, 'load')


@bot.command(name='unload', hidden=True)
@commands.is_owner()
async def unload_command(ctx: GitBotContext, cog: str) -> None:
    await do_cog_op(ctx, cog, 'unload')


@bot.check
async def global_check(ctx: GitBotContext) -> bool:
    if not isinstance(ctx.channel, discord.DMChannel) and ctx.guild.unavailable:
        return False

    return True


@bot.before_invoke
async def before_invoke(ctx: GitBotContext):
    if str(ctx.command) not in bot.mgr.env.no_typing_commands:
        await ctx.channel.typing()


if __name__ == '__main__':
    load_dotenv()
    bot.run(getenv('BOT_TOKEN'))
