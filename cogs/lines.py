import re
from typing import Union
from discord.ext import commands
from ext.decorators import guild_available
from aiohttp import ClientSession

GITHUB = re.compile(r'github\.com/([a-zA-Z0-9-_]+/[A-Za-z0-9_.-]+)/blob/(.+?)/(.+?)#L(\d+)[-~]?L?(\d*)')
GITLAB = re.compile(r'gitlab\.com/([a-zA-Z0-9-_]+/[A-Za-z0-9_.-]+)/-/blob/(.+?)/(.+?)#L(\d+)-?(\d*)')


async def compile_github_link(data: tuple) -> str:
    assert len(data) == 5, "expected a 5 item tuple, got " + str(len(data))
    return f"https://raw.githubusercontent.com/{data[0]}/{data[1]}/{data[2]}"


async def compile_gitlab_link(data: tuple) -> str:
    assert len(data) == 5, "expected a 5 item tuple, got " + str(len(data))
    return f"https://gitlab.com/{data[0]}/-/raw/{data[1]}/{data[2]}"


class Lines(commands.Cog):
    def __init__(self, client):
        self.client: commands.Bot = client
        self.ses: ClientSession = ClientSession(loop=self.client.loop)
        self.e: str = "<:ge:767823523573923890>"

    async def compile_text(self, url: str, data: tuple) -> Union[str, None]:
        content = await (await self.ses.get(url)).text(encoding='utf-8')

        extension = url[url.rindex('.') + 1:]
        extension = 'js' if extension == 'ts' else extension

        lines_ = content.splitlines(keepends=True)
        lines = []
        for line in lines_[int(data[3]) - 1:int(data[4]) if data[4] != '' else int(data[3])]:
            if line == '\r\n' or line.endswith('\n'):
                lines.append(line)
                continue
            lines.append(f"{line}\n")

        text = ''.join(lines)
        result = f"```{extension}\n{text}\n```"
        if result == f"```{extension}\n\n```":
            return None
        return result

    @guild_available()
    @commands.command(name='--lines', aliases=['-lines', 'lines', 'line', '-line', '--line'])
    @commands.cooldown(15, 30, commands.BucketType.member)
    async def lines_command(self, ctx, link: str) -> None:
        github_match = re.findall(GITHUB, link)
        gitlab_match = re.findall(GITLAB, link)
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
        return await ctx.send(result)


def setup(client):
    client.add_cog(Lines(client))
