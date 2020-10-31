import discord.ext.commands as commands


class Errors(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.e: str = "<:ge:767823523573923890>"

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"{self.e}  You didn't pass in all of the arguments, **use** `git --help` **for info.**")
        elif isinstance(error, commands.CommandOnCooldown):
            msg = self.e + " " + '**You\'re on cooldown!** Please try again in {:.2f}s'.format(error.retry_after)
            await ctx.send(msg)


def setup(client):
    client.add_cog(Errors(client))
