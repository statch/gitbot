from os import getenv
from typing import Union, List, Optional
import aiohttp
import gidgethub.aiohttp as gh
from dotenv import load_dotenv
from gidgethub import BadRequest
from datetime import date, datetime
from collections import namedtuple

BASE_URL: str = 'https://api.github.com'
GRAPHQL: str = 'https://api.github.com/graphql'


class API:
    """Main Class used to interact with the GitHub API"""

    def __init__(self):
        load_dotenv()
        self.token: str = getenv("GITHUB")
        self.ses: aiohttp.ClientSession = aiohttp.ClientSession()
        self.gh = gh.GitHubAPI(session=self.ses, requester="itsmewulf, Python 3.7",
                               oauth_token=self.token)
		
	async def ghprofile_stats(self, name: str) -> Union[namedtuple, None]:
		if '/' in name or '&' in name:
			return None
		res = await (await self.ses.get('https://api.ghprofile.me/historic/view?username=%s' % name)).json()
		period: dict = dict(res['payload']['period'])
		if not res['success'] or sum([int(v) for v in period.values()]) == 0:
			return None
		else:
			Stats = namedtuple('Stats', ['all_time', 'month', 'fortnight', 'week', 'day', 'hour'])
			return Stats(*[int(v) for v in period.values()])

    async def get_ratelimit(self) -> dict:
        return await self.gh.getitem("/rate_limit")

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
    async def get_user(self, user: str):
        year_start: str = f'{date.today().year}-01-01T00:00:30Z'
        to: str = datetime.utcnow().strftime('%Y-%m-%dT%XZ')
        query: str = """
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
        """.format(user=user, from_=year_start, to=to)
        res = await self.ses.post(GRAPHQL,
                                  json={"query": query},
                                  headers={"Authorization": f"token {self.token}"})

        data = await res.json()
        if not data['data']['user']:
            return None

        data_ = data['data']['user']['contributionsCollection']['contributionCalendar']
        data['data']['user']['contributions'] = data_['totalContributions'], data_['weeks'][-1]['contributionDays'][-1][
            'contributionCount']
        data = data['data']['user']
        del data['contributionsCollection']
        data['organizations'] = data['organizations']['totalCount']
        data['public_repos'] = data['repositories']['totalCount']
        data['following'] = data['following']['totalCount']
        data['followers'] = data['followers']['totalCount']
        return dict(data)

