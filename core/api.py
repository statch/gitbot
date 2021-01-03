import aiohttp
import gidgethub.aiohttp as gh
from os import getenv
from typing import Union, List, Optional
from dotenv import load_dotenv
from gidgethub import BadRequest
from datetime import date, datetime
from collections import namedtuple

BASE_URL: str = 'https://api.github.com'
GRAPHQL: str = 'https://api.github.com/graphql'
GhStats = namedtuple('Stats', ['all_time', 'month', 'fortnight', 'week', 'day', 'hour'])


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
            return GhStats(*[int(v) for v in period.values()])

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

    async def get_repo_zip(self, repo: str) -> Optional[bytes]:
        if '/' not in repo:
            return None
        try:
            res = await self.ses.get(BASE_URL + f"/repos/{repo}/zipball",
                                     headers={"Authorization": f"token {self.token}"})
            if res.status == 200:
                return await res.content.read()
            return None
        except BadRequest:
            return None

    async def get_issue(self, repo: str, number: int) -> Union[dict, str]:
        if '/' not in repo or repo.count('/') > 1:
            return 'repo'

        split: list = repo.split('/')
        owner: str = split[0]
        repository: str = split[1]

        query: str = """
        {{
          repository(name: "{repo_name}", owner: "{owner_name}") {{
            issue(number: {issue_number}) {{
              author{{
                login
                url
                avatarUrl
              }}
              url
              createdAt
              closed
              closedAt
              bodyText
              title 
              state
              comments {{
                totalCount
              }}
              participants {{
                totalCount
              }}
              assignees {{
                totalCount
              }}
              labels(first: 100) {{
                edges{{
                  node{{
                    name
                  }}
                }}
              }}
            }}
          }}
        }}
        """.format(repo_name=repository, owner_name=owner, issue_number=number)

        res = await self.ses.post(GRAPHQL,
                                  json={"query": query},
                                  headers={"Authorization": f"token {self.token}"})

        data: dict = dict(await res.json())

        if "errors" in data:
            if not data['data']['repository']:
                return 'repo'
            return 'number'

        data: dict = data['data']

        comment_count: int = data['repository']['issue']['comments']['totalCount']
        assignee_count: int = data['repository']['issue']['assignees']['totalCount']
        participant_count: int = data['repository']['issue']['participants']['totalCount']
        del data['repository']['issue']['comments']
        data['repository']['issue']['body']: str = data['repository']['issue']['bodyText']
        del data['repository']['issue']['bodyText']
        data['repository']['issue']['commentCount']: int = comment_count
        data['repository']['issue']['assigneeCount']: int = assignee_count
        data['repository']['issue']['participantCount']: int = participant_count
        data['repository']['issue']['labels']: list = [lb['node']['name'] for lb in
                                                       list(data['repository']['issue']['labels']['edges'])]
        return data['repository']['issue']

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
