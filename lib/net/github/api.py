import aiohttp
import asyncio
import functools
import gidgethub.aiohttp as gh
from sys import version_info
from typing import Union, Optional, Callable, Coroutine, Any
from gidgethub import BadRequest, QueryError
from datetime import date, datetime
from itertools import cycle
from lib.structs import DirProxy, GhProfileData, TypedCache, CacheSchema
from lib.utils.decorators import normalize_repository

YEAR_START: str = f'{date.today().year}-01-01T00:00:30Z'
BASE_URL: str = 'https://api.github.com'
DISCORD_UPLOAD_SIZE_THRESHOLD_BYTES: int = int(7.85 * (1024 ** 2))  # 7.85mb
github_object_cache: TypedCache = TypedCache(CacheSchema(key=str, value=dict), maxsize=64, max_age=600)


def github_cached(func: Union[Callable, Coroutine]) -> Union[Callable, Coroutine]:
    @functools.wraps(func)
    async def wrapper(*args: tuple, **kwargs: dict) -> Any:
        # actually 2nd cause we're working with methods
        first_arg_or_arbitrary_kwarg = args[1] if args else next(iter(kwargs))
        if cached := github_object_cache.get(first_arg_or_arbitrary_kwarg):
            return cached
        result: Any = await func(*args, **kwargs)
        if isinstance(result, (dict, list)):
            github_object_cache[first_arg_or_arbitrary_kwarg] = result
        return result

    return wrapper


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
        requester: str = requester + '; Python {v.major}.{v.minor}.{v.micro}'.format(v=version_info)
        self.__tokens: tuple = tokens
        self._queries: DirProxy = DirProxy('./data/queries/', ('.gql', '.graphql'))
        self.tokens: cycle = cycle(t for t in tokens if t is not None)
        self.ses: aiohttp.ClientSession = aiohttp.ClientSession()
        self.gh: gh.GitHubAPI = gh.GitHubAPI(session=self.ses, requester=requester, oauth_token=self.__token)

    @property
    def __token(self) -> str:
        return next(self.tokens)

    async def ghprofile_stats(self, name: str) -> Optional[GhProfileData]:
        if '/' in name or '&' in name:
            return None
        res = await (await self.ses.get(f'https://api.ghprofile.me/historic/view?username={name}')).json()
        period: dict = dict(res['payload']['period'])
        if not res['success'] or sum([int(v) for v in period.values()]) == 0:
            return None
        return GhProfileData(*[int(v) for v in period.values()])

    async def get_ratelimit(self) -> tuple[tuple[dict, ...], int]:
        results: list = []
        for token in self.__tokens:
            data = await (await self.ses.get(f'https://api.github.com/rate_limit',
                                             headers={'Authorization': f'token {token}'})).json()
            results.append(data)
        return tuple(results), len(self.__tokens)

    @github_cached
    async def get_user_repos(self, user: str) -> Optional[list]:
        try:
            return list([x for x in await self.gh.getitem(f'/users/{user}/repos') if x['private'] is False])
        except BadRequest:
            return None

    @github_cached
    async def get_org(self, org: str) -> Optional[dict]:
        try:
            return await self.gh.getitem(f'/orgs/{org}')
        except BadRequest:
            return None

    @github_cached
    async def get_org_repos(self, org: str) -> Union[list[dict], list]:
        try:
            res = list([x for x in await self.gh.getitem(f'/orgs/{org}/repos') if x['private'] is False])
            return res
        except BadRequest:
            return []

    @normalize_repository
    async def get_repo_files(self, repo: str) -> Union[list[dict], list]:
        if repo.count('/') != 1:
            return []
        try:
            return await self.gh.getitem(f'/repos/{repo}/contents')
        except BadRequest:
            return []

    @normalize_repository
    async def get_tree_file(self, repo: str, path: str):
        if repo.count('/') != 1:
            return []
        if path[0] == '/':
            path = path[1:]
        try:
            return await self.gh.getitem(f'/repos/{repo}/contents/{path}')
        except BadRequest:
            return []

    @github_cached
    async def get_user_orgs(self, user: str) -> Union[list[dict], list]:
        try:
            return list(await self.gh.getitem(f'/users/{user}/orgs'))
        except BadRequest:
            return []

    @github_cached
    async def get_org_members(self, org: str) -> Union[list[dict], list]:
        try:
            return list(await self.gh.getitem(f'/orgs/{org}/members'))
        except BadRequest:
            return []

    @github_cached
    async def get_user_gists(self, user: str):
        try:
            data = await self.gh.graphql(self._queries.user_gists, **{'Login': user})
        except QueryError:
            return None

        return data['user']

    @github_cached
    async def get_gist(self, gist_id: str) -> Optional[dict]:
        try:
            return dict(await self.gh.getitem(f'/gists/{gist_id}'))
        except BadRequest:
            return None

    @normalize_repository
    async def get_repo_zip(self,
                           repo: str,
                           size_threshold: int = DISCORD_UPLOAD_SIZE_THRESHOLD_BYTES) -> Optional[Union[bool, bytes]]:
        if '/' not in repo or repo.count('/') > 1:
            return None
        res = await self.ses.get(BASE_URL + f'/repos/{repo}/zipball',
                                 headers={'Authorization': f'token {self.__token}'})
        if res.status == 200:
            try:
                await res.content.readexactly(size_threshold)
            except asyncio.IncompleteReadError as read:
                return read.partial
            else:
                return False
        return None

    @normalize_repository
    async def get_latest_release(self, repo: str) -> Optional[dict]:
        if len(_split := repo.split('/')) == 2:
            owner, name = _split
        else:
            return None

        try:
            data: dict = await self.gh.graphql(self._queries.release, **{'Name': name, 'Owner': owner})
        except QueryError:
            return None

        data = data['repository']
        data['release'] = data['releases']['nodes'][0] if data['releases']['nodes'] else None
        data['color'] = int(data['primaryLanguage']['color'][1:], 16) if data['primaryLanguage'] else 0xefefef
        del data['primaryLanguage']
        del data['releases']
        return data

    @normalize_repository
    @github_cached
    async def get_repo(self, repo: str) -> Optional[dict]:
        split: list = repo.split('/')
        if len(split) == 2:
            owner: str = split[0]
            repository: str = split[1]

            try:
                data: dict = await self.gh.graphql(self._queries.repo, **{'Name': repository, 'Owner': owner})
            except QueryError:
                return None

            data = data['repository']
            data['languages'] = data['languages']['totalCount']
            data['topics'] = (data['repositoryTopics']['nodes'], data['repositoryTopics']['totalCount'])
            data['graphic'] = data['openGraphImageUrl'] if data['usesCustomOpenGraphImage'] else None
            data['release'] = data['releases']['nodes'][0]['tagName'] if data['releases']['nodes'] else None
            return data

    @normalize_repository
    async def get_pull_request(self,
                               repo: str,
                               number: int,
                               data: Optional[dict] = None) -> Union[dict, str]:
        if not data:
            if repo.count('/') != 1:
                return 'repo'
            split: list = repo.split('/')
            owner: str = split[0]
            repository: str = split[1]

            try:
                data = await self.gh.graphql(self._queries.pull_request, **{'Name': repository,
                                                                            'Owner': owner,
                                                                            'Number': number})
            except QueryError as e:
                if 'number' in str(e):
                    return 'number'
                return 'repo'
        data: dict = data['repository']['pullRequest'] if 'repository' in data else data
        data['labels']: list = [lb['node']['name'] for lb in data['labels']['edges']]
        data['assignees']['users'] = [(u['node']['login'], u['node']['url']) for u in data['assignees']['edges']]
        data['reviewers'] = {}
        data['reviewers']['users'] = [
            (o['node']['requestedReviewer']['login'] if 'login' in o['node']['requestedReviewer'] else
             o['node']['requestedReviewer']['name'], o['node']['requestedReviewer']['url']) for o
            in data['reviewRequests']['edges']]
        data['reviewers']['totalCount'] = data['reviewRequests']['totalCount']
        data['participants']['users'] = [(u['node']['login'], u['node']['url']) for u in
                                         data['participants']['edges']]
        return data

    @normalize_repository
    async def get_last_pull_requests_by_state(self,
                                              repo: str,
                                              last: int = 10,
                                              state: str = 'OPEN') -> Optional[list[dict]]:
        if repo.count('/') != 1:
            return None

        split: list = repo.split('/')
        owner: str = split[0]
        repository: str = split[1]

        try:
            data: dict = await self.gh.graphql(self._queries.pull_requests, **{'Name': repository,
                                                                               'Owner': owner,
                                                                               'States': state,
                                                                               'Last': last})
        except QueryError:
            return None
        return data['repository']['pullRequests']['nodes']

    @normalize_repository
    async def get_issue(self,
                        repo: str,
                        number: int,
                        data: Optional[dict] = None,  # If data isn't None, this method simply acts as a parser
                        had_keys_removed: bool = False) -> Union[dict, str]:
        if not data:
            if repo.count('/') != 1:
                return 'repo'

            split: list = repo.split('/')
            owner: str = split[0]
            repository: str = split[1]

            try:
                data: dict = await self.gh.graphql(self._queries.issue, **{'Name': repository,
                                                                           'Owner': owner,
                                                                           'Number': number})
            except QueryError as e:
                if 'number' in str(e):
                    return 'number'
                return 'repo'
        if isinstance(data, dict):
            if not had_keys_removed:
                data: dict = data['repository']['issue']
            comment_count: int = data['comments']['totalCount']
            assignee_count: int = data['assignees']['totalCount']
            participant_count: int = data['participants']['totalCount']
            del data['comments']
            data['body']: str = data['bodyText']
            del data['bodyText']
            data['commentCount']: int = comment_count
            data['assigneeCount']: int = assignee_count
            data['participantCount']: int = participant_count
            data['labels']: list = [lb['name'] for lb in list(data['labels']['nodes'])]
        return data

    @normalize_repository
    async def get_last_issues_by_state(self, repo: str, last: int = 10, state: str = 'OPEN') -> Optional[list[dict]]:
        if repo.count('/') != 1:
            return None
        split: list = repo.split('/')
        owner: str = split[0]
        repository: str = split[1]

        try:
            data: dict = await self.gh.graphql(self._queries.issues, **{'Name': repository,
                                                                        'Owner': owner,
                                                                        'States': state,
                                                                        'Last': last})
        except QueryError:
            return None
        return data['repository']['issues']['nodes']

    @github_cached
    async def get_user(self, user: str):
        try:
            data = await self.gh.graphql(self._queries.user, **{'Login': user,
                                                                'FromTime': YEAR_START,
                                                                'ToTime': datetime.utcnow().strftime('%Y-%m-%dT%XZ')})
        except QueryError:
            return None
        data_ = data['user']['contributionsCollection']['contributionCalendar']
        data['user']['contributions'] = data_['totalContributions'], data_['weeks'][-1]['contributionDays'][-1][
            'contributionCount']
        data = data['user']
        del data['contributionsCollection']
        data['organizations'] = data['organizations']['totalCount']
        data['public_repos'] = data['repositories']['totalCount']
        data['following'] = data['following']['totalCount']
        data['followers'] = data['followers']['totalCount']
        return data
