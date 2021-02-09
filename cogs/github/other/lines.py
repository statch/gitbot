import re
from ext import regex
from typing import Union
from discord.ext import commands
from aiohttp import ClientSession


async def compile_github_link(data: tuple) -> str:
    return f"https://raw.githubusercontent.com/{data[0]}/{data[1]}/{data[2]}"


async def compile_gitlab_link(data: tuple) -> str:
    return f"https://gitlab.com/{data[0]}/-/raw/{data[1]}/{data[2]}"


class Lines(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.ses: ClientSession = ClientSession(loop=self.bot.loop)
        self.e: str = "<:ge:767823523573923890>"
        self.errors: dict = {
            0: f'{self.e}  I cannot show **more than 25 lines**, sorry!',
            1: f'{self.e}  There **isn\'t any content** on these lines!',
            2: self.e + '  That {0} is **private or otherwise innacessible.**',
            3: self.e + '  That {0} **doesn\'t exist!**'
        }

    async def compile_text(self, url: str, data: tuple) -> Union[str, int]:
        if data[4]:
            if abs(int(data[3]) - int(data[4])) > 25:
                return 0

        res = await self.ses.get(url)
        content: str = await res.text(encoding='utf-8')

        if res.status == 404 or '<title>Checking your Browser - GitLab</title>' in content:
            return 3

        lines_: list = content.splitlines(keepends=True)

        if not data[4] and lines_[int(data[3]) - 1] == '\n':  # if the request is a single, empty line
            return 1

        extension: str = url[url.rindex('.') + 1:]
        extension: str = 'js' if extension == 'ts' else extension

        lines: list = []
        for line in lines_[int(data[3]) - 1:int(data[4]) if data[4] != '' else int(data[3])]:
            if line == '\r\n' or line.endswith('\n'):
                lines.append(line)
                continue
            lines.append(f"{line}\n")

        text: str = ''.join(lines)
        result: str = f"```{extension}\n{text}\n```"

        return result

    @commands.command(name='--lines', aliases=['-lines', 'lines', 'line', '-line', '--line'])
    @commands.cooldown(15, 30, commands.BucketType.member)
    async def lines_command(self, ctx: commands.Context, link: str) -> None:
        github_match: list = re.findall(regex.GITHUB_LINES_RE, link)
        gitlab_match: list = re.findall(regex.GITLAB_LINES_RE, link)
        if github_match:
            result: str = await self.handle_match(github_match[0])
            platform_term: str = 'repository'
        elif gitlab_match:
            result: str = await self.handle_match(gitlab_match[0], 'gitlab')
            platform_term: str = 'project'
        else:
            await ctx.send(f"{self.e}  The link has to be a GitHub or GitLab URL **mentioning lines!**")
            return

        if isinstance(result, str):
            await ctx.send(result)
        elif isinstance(result, int):
            await ctx.send(self.errors[result].format(platform_term))

    async def handle_match(self, match: tuple, type_: str = 'github') -> str:
        if type_ == 'github':
            url: str = await compile_github_link(match)
        else:
            url: str = await compile_gitlab_link(match)

        return await self.compile_text(url, match)


def setup(bot):
    bot.add_cog(Lines(bot))
