from os import getenv
from typing import Union, List, Optional
import aiohttp
import gidgethub.aiohttp as gh
from dotenv import load_dotenv
from gidgethub import BadRequest
from datetime import date, datetime

BASE_URL: str = 'https://api.github.com'
GRAPHQL: str = 'https://api.github.com/graphql'

with open('./graphql/contribution_count.txt') as f:
    contrib_query = str(''.join(f.readlines()))


def parse_contrib_graphql(user):
    year_start: str = f'{date.today().year}-01-01T00:00:30Z'
    to: str = datetime.utcnow().strftime('%Y-%m-%dT%XZ')
    return contrib_query.replace("%USER%", f'"{user}"', 1).replace('%FROM%', f'"{year_start}"', 1).replace('%TO%',
                                                                                                           f'"{to}"', 1)


class API:
    """Main Class used to interact with the GitHub API"""

    def __init__(self):
        load_dotenv()
        self.token: str = getenv("GITHUB")
        self.ses: aiohttp.ClientSession = aiohttp.ClientSession()
        self.gh = gh.GitHubAPI(session=self.ses, requester="itsmewulf, Python 3.7",
                               oauth_token=self.token)

    async def get_ratelimit(self) -> dict:
        return await self.gh.getitem("/rate_limit")

    async def get_user(self, user: str) -> Optional[dict]:
        try:
            return await self.gh.getitem(f"/users/{user}")
        except BadRequest:
            return None

    async def get_user_repos(self, user: str) -> Optional[list]:
        try:
            return list([x for x in await self.gh.getitem(f"/users/{user}/repos") if x['private'] is False])
        except BadRequest:
            return None

    async def get_org(self, org: str) -> Optional[dict]:
        try:
            return await self.gh.getitem(f"/orgs/{org}")
        except BadRequest:
            return None

    async def get_org_repos(self, org: str) -> Union[List[dict], list]:
        try:
            res = list([x for x in await self.gh.getitem(f"/orgs/{org}/repos") if x['private'] is False])
            return res
        except BadRequest:
            return []

    async def get_repo(self, repo: str) -> Optional[dict]:
        if '/' not in repo:
            return None
        try:
            repo: dict = await self.gh.getitem(f"/repos/{repo}")
            return repo if repo['private'] is False else None
        except BadRequest:
            return None

    async def get_repo_files(self, repo: str) -> Union[List[dict], list]:
        if '/' not in repo:
            return []
        try:
            return await self.gh.getitem(f"/repos/{repo}/contents")
        except BadRequest:
            return []

    async def get_tree_file(self, repo: str, path: str):
        if '/' not in repo:
            return []
        if path[0] != '/':
            path = '/' + str(path)
        try:
            return await self.gh.getitem(f"/repos/{repo}/contents{path}")
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

    async def get_user_gists(self, user: str) -> Union[List[dict], list]:
        try:
            return list(await self.gh.getitem(f"/users/{user}/gists"))
        except BadRequest:
            return []

    async def get_gist(self, gist_id: str) -> Optional[dict]:
        try:
            return dict(await self.gh.getitem(f"/gists/{gist_id}"))
        except BadRequest:
            return None

    # GraphQL
    async def get_contribution_count(self, user: str) -> Union[tuple, None]:
        res = await self.ses.post(GRAPHQL,
                                  json={"query": parse_contrib_graphql(user=user)},
                                  headers={"Authorization": f"token {self.token}"})
        try:
            data = dict(await res.json())['data']['user']['contributionsCollection']['contributionCalendar']
            return data['totalContributions'], data['weeks'][-1]['contributionDays'][-1]['contributionCount']
        except (KeyError, TypeError):
            return None
