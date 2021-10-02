import discord.ext.commands as commands
import discord
import datetime as dt
import ast
from lib.utils.decorators import restricted, gitbot_command
from lib.globs import Git, Mgr
from lib.structs import GitBotEmbed


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

    @restricted()
    @gitbot_command(name='dispatch', aliases=['event'])
    async def event_dispatch_command(self, ctx: commands.Context, event: str) -> None:
        event = event.lower().replace('on_', '', 1)
        cor = {
            'guild_join': ctx.guild,
            'guild_remove': ctx.guild,
            'member_join': ctx.author,
            'member_remove': ctx.author
        }
        if (e := cor.get(event)) is not None:
            self.bot.dispatch(event, e)
            await ctx.success(f'Dispatched event `{event}`')
        else:
            await ctx.err(f'Failed to dispatch event `{event}`')

    @restricted()
    @gitbot_command(name='ratelimit', aliases=['rate'])
    async def ratelimit_command(self, ctx: commands.Context) -> None:
        data = await Git.get_ratelimit()
        rate = data[0]
        embed: GitBotEmbed = GitBotEmbed(
            title=f'{Mgr.e.err}  Rate-limiting'
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

    @commands.is_owner()
    @restricted()
    @gitbot_command(name='eval')
    async def eval_command(self, ctx: commands.Context, *, cmd: str) -> None:
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
                'Mgr': Mgr,
                '__import__': __import__
            }
            exec(compile(parsed, filename='<ast>', mode='exec'), env)  # pylint: disable=exec-used

            result = (await eval(f'{fn_name}()', env))  # pylint: disable=eval-used
            try:
                await ctx.send(result)
            except discord.errors.HTTPException:
                await ctx.send('Evaluation successful, no output.')


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Debug(bot))
