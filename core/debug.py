import discord.ext.commands as commands
import discord
import datetime as dt
import ast
from ext.decorators import is_me
from core.globs import Git


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
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot
        self.emoji: str = '<:github:772040411954937876>'
        self.e: str = '<:ge:767823523573923890>'

    @is_me()
    @commands.command(name='dispatch', aliases=['--event', '--dispatch', 'event'])
    async def manually_trigger_event(self, ctx: commands.Context, event: str) -> None:
        event = event.lower().replace('on_', '', 1)
        cor = {
            'guild_join': ctx.guild,
            'guild_remove': ctx.guild,
            'member_join': ctx.author,
            'member_remove': ctx.author
        }
        if cor.get(event, None) is not None:
            e = cor.get(event, None)
            self.bot.dispatch(event, e)
            await ctx.send(f'{self.emoji} Dispatched event `{event}`')
        else:
            await ctx.send(f'{self.e}  Failed to dispatch event `{event}`')

    @is_me()
    @commands.command(aliases=['--rate', '--ratelimit'])
    async def rate(self, ctx: commands.Context) -> None:
        data = await Git.get_ratelimit()
        rate = data[0]
        embed = discord.Embed(
            color=0xefefef,
            title=f'{self.e}  Rate-limiting',
            description=None
        )
        graphql = [g['resources']['graphql'] for g in rate]
        used_gql = sum(g['used'] for g in graphql)
        rest = [r['rate'] for r in rate]
        used_rest = sum(r['used'] for r in rest)
        search = [s['resources']['search'] for s in rate]
        used_search = sum(s['used'] for s in search)
        embed.add_field(name='REST',
                        value=f"{used_rest}/{data[1] * 5000}\n\
                        `{dt.datetime.fromtimestamp(rest[0]['reset']).strftime('%X')}`")
        embed.add_field(name='GraphQL',
                        value=f"{used_gql}/{data[1] * 5000}\n\
                        `{dt.datetime.fromtimestamp(graphql[0]['reset']).strftime('%X')}`")
        embed.add_field(name='Search',
                        value=f"{used_search}/{data[1] * 30}\n\
                        `{dt.datetime.fromtimestamp(search[0]['reset']).strftime('%X')}`")
        await ctx.send(embed=embed)

    @commands.command()
    @commands.is_owner()
    @is_me()
    async def eval(self, ctx: commands.Context, *, cmd: str) -> None:
        if ctx.message.author.id == 548803750634979340:
            fn_name = '_eval_expr'

            cmd = cmd.strip('` ')

            cmd = "\n".join(f'    {i}' for i in cmd.splitlines())

            body: str = f'async def {fn_name}():\n{cmd}'

            parsed = ast.parse(body)
            body = parsed.body[0].body

            insert_returns(body)

            env = {
                'bot': self.bot,
                'discord': discord,
                'commands': commands,
                'ctx': ctx,
                'Git': Git,
                '__import__': __import__
            }
            exec(compile(parsed, filename='<ast>', mode='exec'),
                 env)  # pylint: disable=exec-used

            result = (await eval(f'{fn_name}()', env))  # pylint: disable=eval-used
            await ctx.send(result)


def setup(bot):
    bot.add_cog(Debug(bot))
