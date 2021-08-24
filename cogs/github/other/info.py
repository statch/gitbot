from discord.ext import commands
from lib.globs import Mgr
from typing import Optional, Union
from lib.structs import GitCommandData
from lib.utils.decorators import gitbot_command


class Info(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot

    # @gitbot_command(name='info')
    # @commands.cooldown(10, 20, commands.BucketType.user)
    # async def info_command(self, ctx: commands.Context, link: str) -> None:
    #     ref: Optional[Union[tuple, str, GitCommandData]] = await Mgr.get_link_reference(link)
    #     if ref is None:
    #         await ctx.err(ctx.l.info.no_info)
    #     elif not isinstance(ref, GitCommandData) and isinstance(ref[0], str):
    #         if ref[0] == 'repo':
    #             await ctx.err(ctx.l.generic.nonexistent.repo)
    #         elif ref[1] == 'issue':
    #             await ctx.err(ctx.l.generic.nonexistent.issue_number)
    #         else:
    #             await ctx.err(ctx.l.generic.nonexistent.pr_number)
    #     elif isinstance(ref, str):
    #         if ref == 'no-user-of-org':
    #             await ctx.err(ctx.l.generic.nonexistent.user_or_org)
    #         else:
    #             await ctx.err(ctx.l.generic.nonexistent.repo)
    #     else:
    #         setattr(ctx, 'data', ref.data)
    #         cmd: commands.Command = self.bot.get_command(ref.type)
    #         if cmd:
    #             if isinstance(args := ref.args, (tuple, list)):
    #                 await ctx.invoke(cmd, *args)
    #             else:
    #                 await ctx.invoke(cmd, **{list(cmd.params.items())[-1][0]: args})


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Info(bot))
