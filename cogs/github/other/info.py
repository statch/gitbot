from discord.ext import commands
from ext.manager import Manager
from typing import Optional, Union

mgr = Manager()


class Info(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot
        self.e: str = "<:ge:767823523573923890>"
        self.d1: str = mgr.emojis["circle_green"]
        self.d2: str = mgr.emojis["circle_yellow"]
        self.d3: str = mgr.emojis["circle_red"]

    @commands.command(name='info')
    @commands.cooldown(10, 20, commands.BucketType.user)
    async def info_command_group(self, ctx: commands.Context, link: str) -> None:
        ref: Optional[Union[tuple, str, 'GitCommandData']] = await mgr.get_link_reference(link)
        if ref is None:
            await ctx.send(f'{self.e}  I couldn\'t fetch any info regarding the link you provided!')
            return
        if isinstance(ref, tuple) and isinstance(ref[0], str):
            if ref[0] == 'repo':
                await ctx.send(f"{self.e}  This repository **doesn't exist!**")
            elif ref[1] == 'issue':
                await ctx.send(f"{self.e}  An issue with this number **doesn't exist!**")
            else:
                await ctx.send(f"{self.e}  A pull request with this number **doesn't exist!**")
            return
        elif isinstance(ref, str):
            if ref == 'no-user-of-org':
                await ctx.send(f'{self.e}  This user or organization **doesn\'t exist!**')
            else:
                await ctx.send(f'{self.e}  This repository **doesn\'t exist!**')
            return
        setattr(ctx, 'data', ref.data)
        cmd: commands.Command = self.bot.get_command(ref.type)
        if isinstance(args := ref.args, (tuple, list)):
            await ctx.invoke(cmd, *args)
            return
        await ctx.invoke(cmd, args)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Info(bot))
