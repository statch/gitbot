from os import getenv
import aiohttp
import gidgethub.aiohttp as gh
from gidgethub import BadRequest
from dotenv import load_dotenv
from typing import Union


class API:
    """Main Class used to interact with the GitHub API"""

    def __init__(self):
        load_dotenv()
        self.ses = aiohttp.ClientSession()
        self.gh = gh.GitHubAPI(session=self.ses, requester="itsmewulf, Python 3.7",
                               oauth_token=getenv("GITHUB"))

    async def get_ratelimit(self) -> dict:
        return await self.gh.getitem("/rate_limit")

    async def get_user(self, user: str) -> Union[dict, None]:
        try:
            return await self.gh.getitem(f"/users/{user}")
        except BadRequest:
            return None

    async def get_user_repos(self, user: str) -> Union[list, None]:
        try:
            return list([x for x in await self.gh.getitem(f"/users/{user}/repos") if x['private'] is False])
        except BadRequest:
            return None

    async def get_org(self, org: str) -> Union[dict, None]:
        try:
            return await self.gh.getitem(f"/orgs/{org}")
        except BadRequest:
            return None

    async def get_org_repos(self, org: str) -> Union[list, None]:
        try:
            return list([x for x in await self.gh.getitem(f"/orgs/{org}/repos") if x['private'] is False])
        except BadRequest:
            return None

    async def get_repo(self, repo: str) -> Union[dict, None]:
        if '/' not in repo:
            return None
        try:
            repo: dict = await self.gh.getitem(f"/repos/{repo}")
            return repo if repo['private'] is False else None
        except BadRequest:
            return None

    async def get_repo_files(self, repo: str) -> Union[list, None]:
        if '/' not in repo:
            return None
        try:
            raw = await self.gh.getitem(f"/repos/{repo}/contents")
            return list(await raw.json())
        except BadRequest:
            return None

    async def get_user_orgs(self, user: str) -> Union[list, None]:
        try:
            return list(await self.gh.getitem(f"/users/{user}/orgs"))
        except BadRequest:
            return None

    async def get_org_members(self, org: str) -> Union[list, None]:
        try:
            return list(await self.gh.getitem(f"/orgs/{org}/members"))
        except BadRequest:
            return None
