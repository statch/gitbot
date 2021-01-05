import discord.ext.commands as commands
import discord
import ast
from ext.decorators import is_me
from cfg import config
import datetime as dt

Git = config.Git


def insert_returns(body):
    if isinstance(body[-1], ast.Expr):
        body[-1] = ast.Return(body[-1].value)
        ast.fix_missing_locations(body[-1])

    if isinstance(body[-1], ast.If):
        insert_returns(body[-1].body)
        insert_returns(body[-1].orelse)

    if isinstance(body[-1], ast.With):
        insert_returns(body[-1].body)


class Debug(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client: commands.Bot = client
        self.emoji: str = '<:github:772040411954937876>'
        self.e: str = "<:ge:767823523573923890>"

    @is_me()
    @commands.command(name='dispatch', aliases=['--event', '--dispatch', 'event'])
    async def manually_trigger_event(self, ctx: commands.Context, event: str):
        event = event.lower().replace('on_', "", 1)
        cor = {
            "guild_join": ctx.guild,
            "guild_remove": ctx.guild,
            "member_join": ctx.author,
            "member_remove": ctx.author
        }
        if cor.get(event, None) is not None:
            e = cor.get(event, None)
            self.client.dispatch(event, e)
            await ctx.send(f"{self.emoji} Dispatched event `{event}`")
        else:
            await ctx.send(f"{self.e}  Failed to dispatch event `{event}`")

    @is_me()
    @commands.command(aliases=["--rate", "--ratelimit"])
    async def rate(self, ctx) -> None:
        rate = await Git.get_ratelimit()
        embed = discord.Embed(
            color=0xefefef,
            title=f"{self.e}  Rate-limiting",
            description=None
        )
        graphql = rate['resources']['graphql']
        rest = rate['rate']
        search = rate['resources']['search']
        embed.add_field(name="REST",
                        value=f"{rest['used']}/{rate['rate']['limit']}\n\
                        `{dt.datetime.fromtimestamp(rest['reset']).strftime('%X')}`")
        embed.add_field(name='GraphQL',
                        value=f"{graphql['used']}/{graphql['limit']}\n\
                        `{dt.datetime.fromtimestamp(graphql['reset']).strftime('%X')}`")
        embed.add_field(name='Search',
                        value=f"{search['used']}/{search['limit']}\n\
                        `{dt.datetime.fromtimestamp(search['reset']).strftime('%X')}`")
        await ctx.send(embed=embed)

    @commands.command()
    @commands.is_owner()
    @is_me()
    async def eval(self, ctx, *, cmd):
        if ctx.message.author.id == 548803750634979340:
            fn_name = "_eval_expr"

            cmd = cmd.strip("` ")

            cmd = "\n".join(f"    {i}" for i in cmd.splitlines())

            body: str = f"async def {fn_name}():\n{cmd}"

            parsed = ast.parse(body)
            body = parsed.body[0].body

            insert_returns(body)

            env = {
                'client': self.client,
                'discord': discord,
                'commands': commands,
                'ctx': ctx,
                'Git': Git,
                '__import__': __import__
            }
            exec(compile(parsed, filename="<ast>", mode="exec"), env)  # pylint: disable=exec-used

            result = (await eval(f"{fn_name}()", env))  # pylint: disable=eval-used
            await ctx.send(result)


def setup(client):
    client.add_cog(Debug(client))
