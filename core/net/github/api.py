import asyncio
from collections import namedtuple
from datetime import date
from datetime import datetime
from itertools import cycle
from sys import version_info
from typing import AnyStr
from typing import Dict
from typing import List
from typing import Optional
from typing import Union

import aiohttp
import gidgethub.aiohttp as gh
from gidgethub import BadRequest

from ext.datatypes.dir_proxy import DirProxy

YEAR_START: str = f"{date.today().year}-01-01T00:00:30Z"
BASE_URL: str = "https://api.github.com"
GRAPHQL: str = "https://api.github.com/graphql"
GhStats = namedtuple("Stats", "all_time month fortnight week day hour")
SIZE_THRESHOLD_BYTES: int = int(7.85 * (1024**2))  # 7.85mb


class GitHubAPI:
    """
    The main class used to interact with the GitHub API.

    Parameters
    ----------
    tokens: list
        The GitHub access tokens to send requests with.
    requester: str
        A :class:`str` denoting the author of the requests (ex. 'BigNoob420')
    """
    def __init__(self, tokens: tuple, requester: str):
        requester: str = requester + "; Python {v.major}.{v.minor}.{v.micro}".format(
            v=version_info)
        self.__tokens: tuple = tokens
        self._queries: DirProxy = DirProxy("./data/queries/",
                                           (".gql", ".graphql"))
        self.tokens: cycle = cycle(t for t in tokens if t is not None)
        self.ses: aiohttp.ClientSession = aiohttp.ClientSession()
        self.gh: gh.GitHubAPI = gh.GitHubAPI(session=self.ses,
                                             requester=requester,
                                             oauth_token=self.token)

    @property
    def token(self) -> str:
        return next(self.tokens)

    async def post_gql(
        self,
        query: str,
        key: Optional[str] = None,
        complex_: bool = False,
        just_query: bool = False,
    ) -> Union[Dict, AnyStr, None]:
        res: dict = await (await self.ses.post(
            GRAPHQL,
            json={"query": query},
            headers={"Authorization": f"token {self.token}"},
        )).json()
        if just_query:
            return res

        if "errors" in res:
            if complex_:
                if not res["data"]["repository"]:
                    return "repo"
                return "number"
            return None
        res: dict = res["data"]
        if not key:
            return res
        if len(split := key.split()) > 1:
            for key in split:
                res = res[key]
            return res
        return res[key]

    async def ghprofile_stats(self, name: str) -> Union[GhStats, None]:
        if "/" in name or "&" in name:
            return None
        res = await (await self.ses.get(
            f"https://api.ghprofile.me/historic/view?username={name}")).json()
        period: dict = dict(res["payload"]["period"])
        if not res["success"] or sum([int(v) for v in period.values()]) == 0:
            return None
        return GhStats(*[int(v) for v in period.values()])

    async def get_ratelimit(self) -> tuple:
        results: list = []
        for token in self.__tokens:
            data = await (await self.ses.get(
                f"https://api.github.com/rate_limit",
                headers={"Authorization": f"token {token}"},
            )).json()
            results.append(data)
        return tuple(results), len(self.__tokens)

    async def get_user_repos(self, user: str) -> Optional[list]:
        try:
            return list([
                x for x in await self.gh.getitem(f"/users/{user}/repos")
                if x["private"] is False
            ])
        except BadRequest:
            return None

    async def get_org(self, org: str) -> Optional[dict]:
        try:
            return await self.gh.getitem(f"/orgs/{org}")
        except BadRequest:
            return None

    async def get_org_repos(self, org: str) -> Union[List[dict], list]:
        try:
            res = list([
                x for x in await self.gh.getitem(f"/orgs/{org}/repos")
                if x["private"] is False
            ])
            return res
        except BadRequest:
            return []

    async def get_repo_files(self, repo: str) -> Union[List[dict], list]:
        if "/" not in repo:
            return []
        try:
            return await self.gh.getitem(f"/repos/{repo}/contents")
        except BadRequest:
            return []

    async def get_tree_file(self, repo: str, path: str):
        if "/" not in repo:
            return []
        if path[0] == "/":
            path = path[1:]
        try:
            return await self.gh.getitem(f"/repos/{repo}/contents/{path}")
        except BadRequest:
            return []

    async def get_user_orgs(self, user: str) -> Union[List[dict], list]:
        try:
            return list(await self.gh.getitem(f"/users/{user}/orgs"))
        except BadRequest:
            return []

    async def get_org_members(self, org: str) -> Union[List[dict], list]:
        try:
            return list(await self.gh.getitem(f"/orgs/{org}/members"))
        except BadRequest:
            return []

    async def get_user_gists(self, user: str):
        query: str = """
        {{
          user(login: "{user}") {q}}}
        """.format(user=user, q=self._queries.user_gists)

        return await self.post_gql(query, "user")

    async def get_gist(self, gist_id: str) -> Optional[dict]:
        try:
            return dict(await self.gh.getitem(f"/gists/{gist_id}"))
        except BadRequest:
            return None

    async def get_repo_zip(self, repo: str) -> Optional[Union[bool, bytes]]:
        res = await self.ses.get(
            BASE_URL + f"/repos/{repo}/zipball",
            headers={"Authorization": f"token {self.token}"},
        )
        if res.status == 200:
            try:
                await res.content.readexactly(SIZE_THRESHOLD_BYTES)
            except asyncio.IncompleteReadError as read:
                return read.partial
            else:
                return False
        return None

    async def get_latest_release(self, repo: str) -> Optional[dict]:
        split: list = repo.split("/")
        owner: str = split[0]
        name: str = split[1]

        query: str = """
        {{
          repository(name: "{name}", owner: "{owner}") {q}}}
        """.format(owner=owner, name=name, q=self._queries.release)

        data: dict = await self.post_gql(query, "repository")
        if data:
            data["release"] = (data["releases"]["nodes"][0]
                               if data["releases"]["nodes"] else None)
            data["color"] = (int(data["primaryLanguage"]["color"][1:], 16)
                             if data["primaryLanguage"] else 0xEFEFEF)
            del data["primaryLanguage"]
            del data["releases"]
        return data

    async def get_repo(self, repo: str) -> Optional[dict]:
        split: list = repo.split("/")
        owner: str = split[0]
        repository: str = split[1]

        query: str = """
        {{
          repository(name: "{name}", owner: "{owner}") {q}}}
        """.format(owner=owner, name=repository, q=self._queries.repo)

        data: dict = await self.post_gql(query, "repository")
        if data:
            data["languages"] = data["languages"]["totalCount"]
            data["topics"] = (
                data["repositoryTopics"]["nodes"],
                data["repositoryTopics"]["totalCount"],
            )
            data["graphic"] = (data["openGraphImageUrl"]
                               if data["usesCustomOpenGraphImage"] else None)
            data["release"] = (data["releases"]["nodes"][0]["tagName"]
                               if data["releases"]["nodes"] else None)
        return data

    async def get_pull_request(
        self,
        repo: str,
        number: int,
        data: Optional[dict] = None,
        had_keys_removed: bool = False,
    ) -> Union[dict, str]:
        if not data:
            split: list = repo.split("/")
            owner: str = split[0]
            repository: str = split[1]

            query: str = """
            {{
              repository(name: "{name}", owner: "{owner}") {{
                pullRequest(number: {number}) {q}
              }}
            }}
            """.format(
                name=repository,
                owner=owner,
                number=number,
                q=self._queries.pull_request,
            )

            data = await self.post_gql(query,
                                       "repository pullRequest",
                                       complex_=True)
        if isinstance(data, dict):
            if not had_keys_removed:
                data: dict = data["repository"]["pullRequest"]
            data["labels"]: list = [
                l["node"]["name"] for l in data["labels"]["edges"]
            ]
            data["assignees"]["users"] = [(u["node"]["login"],
                                           u["node"]["url"])
                                          for u in data["assignees"]["edges"]]
            data["reviewers"] = {}
            data["reviewers"]["users"] = [(
                o["node"]["requestedReviewer"]["login"]
                if "login" in o["node"]["requestedReviewer"] else
                o["node"]["requestedReviewer"]["name"],
                o["node"]["requestedReviewer"]["url"],
            ) for o in data["reviewRequests"]["edges"]]
            data["reviewers"]["totalCount"] = data["reviewRequests"][
                "totalCount"]
            data["participants"]["users"] = [
                (u["node"]["login"], u["node"]["url"])
                for u in data["participants"]["edges"]
            ]
        return data

    async def get_last_pull_requests_by_state(
            self,
            repo: str,
            last: int = 10,
            state: str = "[OPEN]") -> Optional[List[dict]]:
        if "/" not in repo or repo.count("/") > 1:
            return None

        split: list = repo.split("/")
        owner: str = split[0]
        repository: str = split[1]

        query: str = """
        {{
          repository(name: "{name}", owner: "{owner}") {{
            pullRequests(states: {state}, last: {last}) {{
              nodes {q}
            }}
          }}
        }}
        """.format(
            name=repository,
            owner=owner,
            state=state,
            last=last,
            q=self._queries.pull_request,
        )

        data: dict = await self.post_gql(query)
        if "repository" in data and "pullRequests" in data["repository"]:
            return data["repository"]["pullRequests"]["nodes"]

    async def get_issue(
        self,
        repo: str,
        number: int,
        # If data isn't None, this method simply acts as a parser
        data: Optional[dict] = None,
        had_keys_removed: bool = False,
    ) -> Union[dict, str]:
        if not data:
            if "/" not in repo or repo.count("/") > 1:
                return "repo"

            split: list = repo.split("/")
            owner: str = split[0]
            repository: str = split[1]

            query: str = """
            {{
              repository(name: "{repo_name}", owner: "{owner_name}") {{
                issue(number: {issue_number}) {q}
              }}
            }}
            """.format(
                repo_name=repository,
                owner_name=owner,
                issue_number=number,
                q=self._queries.issue,
            )

            data: dict = await self.post_gql(query, complex_=True)
        if isinstance(data, dict):
            if not had_keys_removed:
                data: dict = data["repository"]["issue"]
            comment_count: int = data["comments"]["totalCount"]
            assignee_count: int = data["assignees"]["totalCount"]
            participant_count: int = data["participants"]["totalCount"]
            del data["comments"]
            data["body"]: str = data["bodyText"]
            del data["bodyText"]
            data["commentCount"]: int = comment_count
            data["assigneeCount"]: int = assignee_count
            data["participantCount"]: int = participant_count
            data["labels"]: list = [
                lb["name"] for lb in list(data["labels"]["nodes"])
            ]
        return data

    async def get_last_issues_by_state(
            self,
            repo: str,
            last: int = 10,
            state: str = "[OPEN]") -> Optional[List[dict]]:
        if "/" not in repo or repo.count("/") > 1:
            return None

        split: list = repo.split("/")
        owner: str = split[0]
        repository: str = split[1]

        query: str = """
        {{
          repository(name: "{name}", owner: "{owner}") {{
            issues(states: {state}, last: {last}) {{
              nodes {q}
            }}
          }}
        }}
        """.format(name=repository,
                   owner=owner,
                   state=state,
                   last=last,
                   q=self._queries.issue)

        data: dict = await self.post_gql(query)
        if "repository" in data and "issues" in data["repository"]:
            return data["repository"]["issues"]["nodes"]

    async def get_user(self, user: str):
        to: str = datetime.utcnow().strftime("%Y-%m-%dT%XZ")
        query: str = """  # This isn't in self._queries because I didn't want to mess around formatting it with dates
        {{
          user(login: "{user}") {{
            createdAt
            company
            location
            bio
            websiteUrl
            avatarUrl
            url
            twitterUsername
            organizations {{
              totalCount
            }}
            followers {{
              totalCount
            }}
            following {{
              totalCount
            }}
            repositories {{
              totalCount
            }}
            contributionsCollection(from: "{from_}", to: "{to}") {{
              contributionCalendar {{
                totalContributions
                weeks {{
                  contributionDays {{
                    contributionCount
                  }}
                }}
              }}
            }}
          }}
        }}
        """.format(user=user, from_=YEAR_START, to=to)

        data = await self.post_gql(query, just_query=True)

        if not data["data"]["user"]:
            return None

        data_ = data["data"]["user"]["contributionsCollection"][
            "contributionCalendar"]
        data["data"]["user"]["contributions"] = (
            data_["totalContributions"],
            data_["weeks"][-1]["contributionDays"][-1]["contributionCount"],
        )
        data = data["data"]["user"]
        del data["contributionsCollection"]
        data["organizations"] = data["organizations"]["totalCount"]
        data["public_repos"] = data["repositories"]["totalCount"]
        data["following"] = data["following"]["totalCount"]
        data["followers"] = data["followers"]["totalCount"]
        return data
