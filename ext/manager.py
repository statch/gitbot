import json
import re
from .datatypes.dir_proxy import DirProxy
from ext import regex as r
from typing import Optional, Union, Callable, Any, Reversible, List, Iterable, Tuple
from fuzzywuzzy import fuzz
from collections import namedtuple

json_path: str = r"./data/"
GitCommandData = namedtuple("GitCommandData", "data type args")


def json_dict(name: str) -> dict:
    to_load = json_path + str(name).lower() + ".json" if name[-5:] != ".json" else ""
    return json.load(open(to_load))


class Manager:
    def __init__(self, github_instance):
        self.git = github_instance
        self.licenses: dict = json_dict("licenses")
        self.emojis: dict = json_dict("emoji")
        self.patterns: tuple = (
            (r.GITHUB_LINES_RE, "lines"),
            (r.GITLAB_LINES_RE, "lines"),
            (r.ISSUE_RE, "issue"),
            (r.PR_RE, "pr"),
            (r.REPO_RE, "repo"),
            (r.USER_ORG_RE, "user_org"),
        )
        self.type_to_func: dict = {
            "repo": self.git.get_repo,
            "user_org": None,
            "issue": self.git.get_issue,
            "pr": self.git.get_pull_request,
            "lines": "lines",
        }

    def correlate_license(self, to_match: str) -> Optional[dict]:
        for i in list(self.licenses):
            match = fuzz.token_set_ratio(to_match, i["name"])
            match1 = fuzz.token_set_ratio(to_match, i["key"])
            match2 = fuzz.token_set_ratio(to_match, i["spdx_id"])
            if any([match > 80, match1 > 80, match2 > 80]):
                return i
        return None

    async def get_link_reference(
        self, link: str
    ) -> Optional[Union[GitCommandData, str, tuple]]:
        for pattern in self.patterns:
            match: list = re.findall(pattern[0], link)
            if match:
                match: Union[str, tuple] = match[0]
                action: Optional[Union[Callable, str]] = self.type_to_func[pattern[1]]
                if isinstance(action, str):
                    return GitCommandData(link, "lines", link)
                if isinstance(match, tuple) and action:
                    match: tuple = tuple(
                        i if not i.isnumeric() else int(i) for i in match
                    )
                    obj: Union[dict, str] = await action(match[0], int(match[1]))
                    if isinstance(obj, str):
                        return obj, pattern[1]
                    return GitCommandData(obj, pattern[1], match)
                if not action:
                    if (obj := await self.git.get_user((m := match))) is None:
                        obj: Optional[dict] = await self.git.get_org(m)
                        return (
                            GitCommandData(obj, "org", m)
                            if obj is not None
                            else "no-user-or-org"
                        )
                    return GitCommandData(obj, "user", m)
                repo = await action(match)
                return (
                    GitCommandData(repo, pattern[1], match)
                    if repo is not None
                    else "repo"
                )
        return None

    async def get_most_common(self, items: list) -> Any:
        return max(set(items), key=items.count)

    async def validate_number(self, number: str, items: List[dict]) -> Optional[dict]:
        if number.startswith("#"):
            number: str = number[1:]
        try:
            number: int = int(number)
        except TypeError:
            return None
        matched = [i for i in items if i["number"] == number]
        if matched:
            return matched[0]
        return None

    async def reverse(self, __sequence: Optional[Reversible]) -> Optional[Iterable]:
        if __sequence:
            return type(__sequence)((reversed(__sequence)))
        return None

    async def readdir(self, path: str, ext: Union[str, list, tuple]) -> DirProxy:
        return DirProxy(path=path, ext=ext)
