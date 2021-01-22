import aiohttp
import asyncio
import gidgethub.aiohttp as gh
from sys import version_info
from typing import Union, List, Optional
from gidgethub import BadRequest
from datetime import date, datetime
from collections import namedtuple

BASE_URL: str = 'https://api.github.com'
GRAPHQL: str = 'https://api.github.com/graphql'
GhStats = namedtuple('Stats', 'all_time month fortnight week day hour')
SIZE_THRESHOLD_BYTES: int = int(7.85 * (1024 ** 2))  # 7.85mb


class GitHubAPI:
    """
    The main class used to interact with the GitHub API.

    Parameters
    ----------
    token: str
        The GitHub access token to send requests with.
    requester: str
        A :class:`str` denoting the author of the requests (ex. 'BigNoob420')
    """

    def __init__(self, token: str, requester: str):
        requester: str = requester + '; Python {v.major}.{v.minor}.{v.micro}'.format(v=version_info)
        self.token: str = token
        self.ses: aiohttp.ClientSession = aiohttp.ClientSession()
        self.gh = gh.GitHubAPI(session=self.ses,
                               requester=requester,
                               oauth_token=self.token)

    async def ghprofile_stats(self, name: str) -> Union[namedtuple, None]:
        if '/' in name or '&' in name:
            return None
        res = await (await self.ses.get(f'https://api.ghprofile.me/historic/view?username={name}')).json()
        period: dict = dict(res['payload']['period'])
        if not res['success'] or sum([int(v) for v in period.values()]) == 0:
            return None
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
        if path[0] == '/':
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
          user(login: "{user}") {{
            url
            login
            gists(last: 10) {{
              totalCount
              nodes {{
                id
                stargazerCount
                name 
                description
                updatedAt
                createdAt
                url 
                comments {{
                    totalCount
                }}
                files {{
                  name
                  extension
                  language {{
                    color
                  }}
                }}
              }}
            }}
          }}
        }}
        """.format(user=user)

        res = await self.ses.post(GRAPHQL,
                                  json={"query": query},
                                  headers={"Authorization": f"token {self.token}"})

        data: dict = await res.json()

        if 'errors' in data:
            return None
        data = data['data']['user']

        return data

    async def get_gist(self, gist_id: str) -> Optional[dict]:
        try:
            return dict(await self.gh.getitem(f"/gists/{gist_id}"))
        except BadRequest:
            return None

    async def get_repo_zip(self, repo: str) -> Optional[Union[bool, bytes]]:
        res = await self.ses.get(BASE_URL + f"/repos/{repo}/zipball",
                                 headers={"Authorization": f"token {self.token}"})

        if res.status == 200:
            try:
                await res.content.readexactly(SIZE_THRESHOLD_BYTES)
            except asyncio.IncompleteReadError as read:
                return read.partial
            else:
                return False
        return None

    async def get_repo(self, repo: str) -> Optional[dict]:
        split: list = repo.split('/')
        owner: str = split[0]
        repository: str = split[1]

        query: str = """
        {{
          repository(name: "{name}", owner: "{owner}") {{
            url 
            forkCount
            openGraphImageUrl
            usesCustomOpenGraphImage
            createdAt
            description
            isFork
            owner {{
              avatarUrl
            }}
            parent {{
              nameWithOwner
              url
            }}
            releases(last: 1) {{
              totalCount
              nodes {{
                tagName
              }}
            }}
            repositoryTopics(first: 10) {{
              totalCount
              nodes {{
                topic {{
                  name
                }}
                url
              }}
            }}
            issues(states: OPEN) {{
              totalCount
            }}
            codeOfConduct {{
              name
              url
            }}
            licenseInfo {{
              name
              nickname 
            }}
            primaryLanguage{{
              name
              color
            }}
            languages {{
              totalCount
            }}
            homepageUrl
            stargazers {{
              totalCount
            }}
            watchers {{
              totalCount
            }}
          }}
        }}
        """.format(owner=owner, name=repository)

        res = await self.ses.post(GRAPHQL,
                                  json={"query": query},
                                  headers={"Authorization": f"token {self.token}"})

        data: dict = dict(await res.json())

        if "errors" in data:
            return None

        data = data['data']['repository']
        data['languages'] = data['languages']['totalCount']
        data['topics'] = (data['repositoryTopics']['nodes'], data['repositoryTopics']['totalCount'])
        data['graphic'] = data['openGraphImageUrl'] if data['usesCustomOpenGraphImage'] else None
        data['release'] = data['releases']['nodes'][0]['tagName'] if data['releases']['nodes'] else None

        return data

    async def get_pull_request(self, repo: str, number: int) -> Union[dict, str]:
        split: list = repo.split('/')
        owner: str = split[0]
        repository: str = split[1]

        query: str = """
        {{
          repository(name: "{name}", owner: "{owner}") {{
            pullRequest(number: {number}) {{
              title
              url
              isCrossRepository
              state
              createdAt
              closed
              closedAt
              bodyText
              changedFiles
              commits(first: 250) {{
                totalCount
              }}
              additions
              deletions
              author {{
                login 
                url
                avatarUrl
              }}
              comments {{
                totalCount
              }}
              assignees(first: 100) {{
                totalCount
                edges {{
                  node {{
                    login
                    url
                  }}
                }}
              }}
              reviews(first: 100) {{
                totalCount
              }}
              participants(first: 100){{
                totalCount
                edges {{
                  node {{
                    login
                    url
                  }}
                }}
              }}
              reviewRequests(first: 100) {{
                totalCount
                edges {{
                  node {{
                    requestedReviewer {{
                      ... on User {{
                        login
                        url
                      }}
                      ... on Team {{
                        name
                        url
                      }}
                      ... on Mannequin {{
                        login
                        url
                      }}
                    }}
                  }}
                }}
              }}
              labels(first: 100) {{
                edges {{
                  node {{
                    name
                  }}
                }}
              }}
            }}
          }}
        }}
        """.format(name=repository, owner=owner, number=number)

        res = await self.ses.post(GRAPHQL,
                                  json={"query": query},
                                  headers={"Authorization": f"token {self.token}"})

        data: dict = dict(await res.json())

        if "errors" in data:
            if not data['data']['repository']:
                return 'repo'
            return 'number'

        data = data['data']['repository']['pullRequest']
        data['labels']: list = [l['node']['name'] for l in data['labels']['edges']]
        data['assignees']['users'] = [(u['node']['login'], u['node']['url']) for u in data['assignees']['edges']]
        data['reviewers'] = {}
        data['reviewers']['users'] = [
            (o['node']['requestedReviewer']['login'] if 'login' in o['node']['requestedReviewer'] else
             o['node']['requestedReviewer']['name'], o['node']['requestedReviewer']['url']) for o
            in data['reviewRequests']['edges']]
        data['reviewers']['totalCount'] = data['reviewRequests']['totalCount']
        data['participants']['users'] = [(u['node']['login'], u['node']['url']) for u in data['participants']['edges']]
        return data

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
