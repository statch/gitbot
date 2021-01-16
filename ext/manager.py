import json
import re
import ext.regex as r
from core import bot_config
from typing import Optional, Union, Callable
from fuzzywuzzy import fuzz
from collections import namedtuple

json_path = r'./data/'
Git = bot_config.Git
GitCommandData = namedtuple('GitObject', 'object type args')


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

    async def get_link_reference(self, link: str) -> Optional[Union[GitCommandData, str, tuple]]:
        for pattern in self.patterns:
            match: list = re.findall(pattern[0], link)
            if match:
                match: Union[str, tuple] = match[0]
                action: Optional[Callable] = self.type_to_func[pattern[1]]
                if isinstance(match, tuple) and action:
                    match: tuple = tuple([i if not i.isnumeric() else int(i) for i in match])
                    obj: Union[dict, str] = await action(match[0], int(match[1]))
                    if isinstance(obj, str):
                        return obj, pattern[1]
                    return GitCommandData(obj, pattern[1], match)
                if not action:
                    if obj := await Git.get_user((m := match)) is None:
                        obj: Optional[dict] = await Git.get_org(m)
                        return GitCommandData(obj, 'org', m) if obj is not None else 'no-user-or-org'
                    else:
                        return GitCommandData(obj, 'user', m)
                repo = await action(match)
                return GitCommandData(repo, 'repo', match) if repo is not None else 'repo'
        return None
