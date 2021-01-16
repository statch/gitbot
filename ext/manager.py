import json
import re
import ext.regex as r
from core import bot_config
from typing import Optional, Tuple, Union, Callable
from fuzzywuzzy import fuzz

json_path = r'./data/'
Git = bot_config.Git


def json_dict(name: str) -> dict:
    to_load = json_path + str(name).lower() + '.json' if name[-5:] != '.json' else ''
    return json.load(open(to_load))


class Manager:
    def __init__(self):
        self.licenses: dict = json_dict("licenses")
        self.emojis: dict = json_dict("emoji")
        self.patterns: tuple = ((r.ISSUE_RE, 'issue'),
                                (r.PR_RE, 'pr'),
                                (r.REPO_RE, 'repo'),
                                (r.USER_ORG_RE, 'user_org'))
        self.type_to_func: dict = {'repo': Git.get_repo,
                                   'user_org': None,
                                   'issue': Git.get_issue,
                                   'pr': Git.get_pull_request}

    def correlate_license(self, to_match: str) -> Optional[dict]:
        for i in list(self.licenses):
            match = fuzz.token_set_ratio(to_match, i["name"])
            match1 = fuzz.token_set_ratio(to_match, i["key"])
            match2 = fuzz.token_set_ratio(to_match, i["spdx_id"])
            if any([match > 80, match1 > 80, match2 > 80]):
                return i
        return None

    async def get_link_reference(self, link: str) -> Optional[Union[Tuple[dict, str], str]]:
        for pattern in self.patterns:
            match: list = re.findall(pattern[0], link)
            if match:
                match: Union[str, tuple] = match[0]
                action: Optional[Callable] = self.type_to_func[pattern[1]]
                if isinstance(match, tuple) and action:
                    return await action(match[0], int(match[1])), pattern[1]
                if not action:
                    if obj := await Git.get_user((m := match)) is None:
                        obj: Optional[dict] = await Git.get_org(m)
                        return obj, 'org' if obj is not None else 'org'
                    else:
                        return obj, 'user'
                return (repo := await action(match)), 'repo' if repo is not None else 'repo'
            return None
