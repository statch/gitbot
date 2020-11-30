from discord.ext import commands
from ext.decorators import is_me
import discord


class Migrator(commands.Cog):
    def __init__(self, client):
        self.client: commands.Bot = client

    @is_me()
    @commands.command()
    async def discriminator(self, ctx):
        discriminators = []
        for guild in self.client.guilds:
            new_discrims = [m.discriminator for m in await guild.fetch_members(limit=None).flatten()]
            discriminators += new_discrims
        with open('./migrations/discriminator.csv', mode='w+', newline='') as file:
            for discrim in discriminators:
                file.write(discrim + '\n')
            file.close()
            await ctx.send('Done!', file=discord.File(fp=file, filename='discrim.csv'))


def setup(client: commands.Bot):
    client.add_cog(Migrator(client))
