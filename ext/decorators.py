from discord.ext import commands


def dev_only() -> commands.Command:
    def pred(ctx: commands.Context) -> bool:
        return ctx.author.id == 548803750634979340

    return commands.check(pred)
