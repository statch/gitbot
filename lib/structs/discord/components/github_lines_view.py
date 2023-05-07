import re
import discord
from typing import TYPE_CHECKING
from lib.utils.regex import GITHUB_LINES_URL_RE, GITLAB_LINES_URL_RE
from cogs.github.other.snippets._snippet_tools import get_text_from_url_and_data, compile_url

if TYPE_CHECKING:
    from lib.structs import GitBotContext


class GitHubLinesView(discord.ui.View):
    """
    View facilitating the viewing of consecutive lines of code from a GitHub line link.
    Meant to only be used in the raw text implementation.
    """

    def __init__(self, ctx: 'GitBotContext', lines_url: str, timeout: int = 180):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self._url: str = lines_url
        self.parsed: re.Match = (re.search(GITHUB_LINES_URL_RE, self._url) or
                                 re.search(GITLAB_LINES_URL_RE, self._url))
        self.l1: int = max(int(self.parsed.group('first_line_number')), 1)
        self.l2: int | None = None or (_opt := self.ctx.bot.mgr.opt)(_opt(_opt(self.parsed.groups(), 5), int), max, 1)
        _joint_args: tuple = (self.ctx, self._url, self.l1, self.l2, self.parsed)
        _fmt = ctx.l.views.button.github_lines.view_from_to.format
        self.add_item(GitHubLinesButton(*_joint_args,
                                        forward=False,
                                        label=_fmt(max(self.l1 - 25, 1), max(self.l1 - 1, 1)),
                                        emoji='⬅️', style=discord.ButtonStyle.gray))
        self.add_item(GitHubLinesButton(*_joint_args,
                                        forward=True,
                                        label=_fmt(max(self.l2 + 1, 1), max(self.l2 + 25, 1)),
                                        emoji='➡️', style=discord.ButtonStyle.gray))


class GitHubLinesButton(discord.ui.Button):
    def __init__(self, ctx: 'GitBotContext', lines_url: str, line_1: int, line_2: int, data: re.Match, forward: bool,
                 **kwargs):
        super().__init__(**kwargs, custom_id=f'github_lines_button_{"forward" if forward else "backward"}')
        self.ctx = ctx
        self._url: str = lines_url
        self.forward: bool = forward
        self.parsed: re.Match = data
        self.l1: int = line_1
        self.l2: int | None = line_2

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        previous_l1, previous_l2 = self.l1, self.l2
        if self.forward:
            if self.l2 is not None:
                self.l1: int = self.l2 + 1
                self.l2 += 25
            else:
                self.l2: int = self.l1 + 25
        else:
            self.l2: int = self.l1 - 1
            self.l1 -= 25
        self.l1, self.l2 = max(self.l1, 1), max(self.l2, 1)
        match self.parsed.group('platform'):
            case 'github':
                if previous_l2 is None:
                    self._url = self._url.replace(f'L{previous_l1}', f'L{self.l1}-L{self.l2}')
                else:
                    self._url = self._url.replace(f'L{previous_l1}-L{previous_l2}', f'L{self.l1}-L{self.l2}')
            case 'gitlab':
                if previous_l2 is None:
                    self._url = self._url.replace(f'#L{[previous_l1]}', f'#L{self.l1}-{self.l2}')
                else:
                    self._url = self._url.replace(f'#L{previous_l1}-L{previous_l2}', f'#L{self.l1}-L{self.l2}')
        new_match = self.parsed.groups()[0:4] + (self.l1, self.l2)
        new, _ = await get_text_from_url_and_data(self.ctx, compile_url(new_match), new_match)
        if new:
            await interaction.message.reply(new, mention_author=False, view=GitHubLinesView(self.ctx, self._url))
