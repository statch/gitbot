# TODO Clean this shit up

import re
import ext.regex as regex
from typing import Union
from discord.ext import commands
from aiohttp import ClientSession


async def compile_github_link(data: tuple) -> str:
    assert len(data) == 5, "expected a 5 item tuple, got " + str(len(data))
    return f"https://raw.githubusercontent.com/{data[0]}/{data[1]}/{data[2]}"


async def compile_gitlab_link(data: tuple) -> str:
    assert len(data) == 5, "expected a 5 item tuple, got " + str(len(data))
    return f"https://gitlab.com/{data[0]}/-/raw/{data[1]}/{data[2]}"


class Lines(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.ses: ClientSession = ClientSession(loop=self.bot.loop)
        self.e: str = "<:ge:767823523573923890>"

    async def compile_text(self, url: str, data: tuple) -> Union[str, bool, None]:
        content = await (await self.ses.get(url)).text(encoding='utf-8')
        lines_ = content.splitlines(keepends=True)

        if data[4] == '' and lines_[int(data[3]) - 1] == '\n':  # if the request is a single, empty line
            return False

        extension = url[url.rindex('.') + 1:]
        extension = 'js' if extension == 'ts' else extension

        lines = []
        for line in lines_[int(data[3]) - 1:int(data[4]) if data[4] != '' else int(data[3])]:
            if line == '\r\n' or line.endswith('\n'):
                lines.append(line)
                continue
            lines.append(f"{line}\n")

        text = ''.join(lines)
        result = f"```{extension}\n{text}\n```"
        if result == f"```{extension}\n\n```" or len(content) == 0:
            return None
        return result

    @commands.command(name='--lines', aliases=['-lines', 'lines', 'line', '-line', '--line'])
    @commands.cooldown(15, 30, commands.BucketType.member)
    async def lines_command(self, ctx: commands.Context, link: str) -> None:
        github_match = re.findall(regex.GITHUB_LINES, link)
        gitlab_match = re.findall(regex.GITLAB_LINES, link)
        if github_match:
            github_match = github_match[0]

            if github_match[4] != '' and abs(int(github_match[3]) - int(github_match[4])) > 25:
                return await ctx.send(f"{self.e}  I cannot show **more than 25 lines**, sorry!")

            try:
                raw_url = await compile_github_link(github_match)
            except AssertionError:
                return await ctx.send(f"{self.e}  Something went wrong while parsing the lines!")

            result = await self.compile_text(raw_url, github_match)
            if not result:
                return await ctx.send(f"{self.e}  That repo is private or otherwise inaccessible.")
        elif gitlab_match:
            gitlab_match = gitlab_match[0]
            if gitlab_match[4] != '' and abs(int(gitlab_match[3]) - int(gitlab_match[4])) > 25:
                return await ctx.send(f"{self.e}  I cannot show **more than 25 lines**, sorry!")

            try:
                raw_url = await compile_gitlab_link(gitlab_match)
            except AssertionError:
                return await ctx.send(f"{self.e}  Something went wrong while parsing the lines!")

            result = await self.compile_text(raw_url, gitlab_match)
            if not result:
                return await ctx.send(f"{self.e}  That project is private or otherwise inaccessible.")
        else:
            return await ctx.send(f"{self.e}  The link isn't a GitHub or GitLab URL!")
        if isinstance(result, bool):
            return await ctx.send
        return await ctx.send(result)


def setup(bot):
    bot.add_cog(Lines(bot))
