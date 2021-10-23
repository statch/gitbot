import re
import io
from typing import Optional
from aiohttp import ClientResponse
from discord.ext import commands
from lib.utils import regex
from lib.globs import Mgr, Carbon


async def handle_url(ctx: commands.Context, url: str, **kwargs) -> tuple:
    match_: tuple = Mgr.opt(re.findall(regex.GITHUB_LINES_URL_RE, url) or re.findall(regex.GITLAB_LINES_URL_RE, url), 0)
    if match_:
        return await get_text_from_url_and_data(ctx, await compile_url(match_), match_, **kwargs)
    return None, ctx.l.snippets.no_lines_mentioned


async def get_text_from_url_and_data(ctx: commands.Context,
                                     url: str,
                                     data: tuple,
                                     max_line_count: int = 25,
                                     wrap_in_codeblock: bool = True) -> Optional[tuple]:
    if data[5]:
        if abs(int(data[4]) - int(data[5])) > max_line_count:
            return None, ctx.fmt('length_limit_exceeded', max_line_count)

    res: ClientResponse = await Mgr.git.ses.get(url)
    content: str = await res.text(encoding='utf-8')

    if '<title>Checking your Browser - GitLab</title>' in content or res.status == 404:
        return None, ctx.fmt('nonexistent', ctx.l.glossary[f'{data[0]}_repo_term'])

    lines_: list = content.splitlines(keepends=True)

    if not data[5] and lines_[int(data[4]) - 1] == '\n':  # if the request is a single, empty line
        return None, ctx.l.snippets.no_content

    extension: str = url[url.rindex('.') + 1:]
    extension: str = 'js' if extension == 'ts' else extension

    lines: list = []
    for line in lines_[int(data[4]) - 1:int(data[5]) if data[5] else int(data[4])]:
        if line == '\r\n' or line.endswith('\n'):
            lines.append(line)
            continue
        lines.append(f'{line}\n')

    text: str = ''.join(lines)
    return f"```{extension}\n{text.rstrip()}\n```" if wrap_in_codeblock else text.rstrip(), None


async def _compile_github_link(data: tuple) -> str:
    return f'https://raw.githubusercontent.com/{data[1]}/{data[2]}/{data[3]}'


async def _compile_gitlab_link(data: tuple) -> str:
    return f'https://gitlab.com/{data[1]}/-/raw/{data[2]}/{data[3]}'


async def gen_carbon_inmemory(code: str) -> io.BytesIO:
    return await (await Carbon.generate_basic_image(code)).memorize()


async def compile_url(match: tuple) -> str:
    if match[0] == 'github':
        return await _compile_github_link(match)
    return await _compile_gitlab_link(match)
