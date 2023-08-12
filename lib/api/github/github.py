# coding: utf-8

"""
An organized way of making requests to the GitHub API, handling errors, caching, sanitization, and more.
~~~~~~~~~~~~~~~~~~~
GitBot backend for interacting with GitHub's API.
:copyright: (c) 2020-present, statch
:license: CC BY-NC-ND 4.0, see LICENSE for more details.
"""

import aiohttp
import asyncio
import functools
import inspect
import gidgethub.aiohttp as gh
from sys import version_info
from typing import Optional, Callable, Any, Literal, TYPE_CHECKING, LiteralString
from gidgethub import BadRequest, QueryError
from datetime import date, datetime
from lib.structs import DirProxy, TypedCache, CacheSchema, DictProxy, SnakeCaseDictProxy
from lib.utils.decorators import normalize_repository, validate_github_name
from lib.typehints import GitHubRepository, GitHubOrganization, GitHubUser
from lib.utils import get_nested_key, get_all_dict_paths, set_nested_key
from cogs.backend.handle.errors._error_tools import log_error_in_discord
from .transformations import *

if TYPE_CHECKING:
    from lib.structs.discord.bot import GitBot

YEAR_START: str = f'{date.today().year}-01-01T00:00:30Z'
DISCORD_UPLOAD_SIZE_THRESHOLD_BYTES: int = int(7.85 * (1024 ** 2))  # 7.85mb

_ReturnDict = SnakeCaseDictProxy | dict
_GitHubAPIQueryWrapOnFailReturnDefaultNotSet = Literal['default_not_set']
_GitHubAPIQueryWrapOnFailReturnDefaultConditionDict = dict[str, str | int | bool | None]

__all__: tuple = ('GitHubAPI', 'GitHubQueryDebugInfo')


def github_cached(func: Callable) -> Callable:
    @functools.wraps(func)
    async def wrapper(*args: tuple, **kwargs: dict) -> Any:
        cache_key: str = f'{id(func)}:{args[1] if args else next(iter(kwargs))}'
        if cached := GitHubAPI.github_object_cache.get(cache_key):
            return cached
        result: Any = await func(*args, **kwargs)
        if isinstance(result, (dict, list)):
            GitHubAPI.github_object_cache[cache_key] = result
        return result

    return wrapper


# decorator to wrap return in snake-case-DictProxy if the return is not None else None; ! use before any other decos !
def _wrap_proxy(func: Callable) -> Callable[..., SnakeCaseDictProxy | None]:
    @functools.wraps(func)
    async def wrapper(*args: tuple, **kwargs: dict) -> Any:
        result: dict | str | None = await func(*args, **kwargs)
        if result is not None and not isinstance(result, str):
            return SnakeCaseDictProxy(result)
        return result

    return wrapper


def _flatten_total_counts(func: Callable) -> Callable[..., DictProxy | SnakeCaseDictProxy | None]:
    """
    Flattens totalCount fields in the response dict by copying the value up one level and setting a "<parent>_count" key.

    :param func: The function to wrap (must return a dict-like interface)
    :return: The wrapped functions output, with the totalCount fields flattened
    """

    @functools.wraps(func)
    async def wrapper(*args: tuple, **kwargs: dict) -> Any:
        result: dict | None = await func(*args, **kwargs)
        if result is not None and isinstance(result, (DictProxy, SnakeCaseDictProxy, dict)):
            result = SnakeCaseDictProxy(result)
            paths: list[tuple[str, ...]] = get_all_dict_paths(result)
            for path in paths:
                if path[-1] == 'totalcount':  # noqa
                    # this dict path contains a totalCount field in the last position -
                    # we flatten it by copying the dict item up one level and renaming the key to <parent>_count.
                    # note that this does not remove the totalCount field from the dict or anything for that matter,
                    # it just makes it easier to access the value.
                    set_nested_key(result, path[:-2] + (f'{path[-2]}_count',), get_nested_key(result, path))
            return result
        return None

    return wrapper


class GitHubQueryDebugInfo:
    __ignorable_error_substrings__: tuple[str, ...] = (
        'Could not resolve to a Repository with the name',
        'Could not resolve to a User with the login',
        'Could not resolve to a Organization with the login',
        'Not Found',
        'Could not resolve to a PullRequest with the number of',
        'Could not resolve to an Issue with the number of',
        'Variable $Oid of type GitObjectID! was provided invalid value'
    )

    """
    A class used to store information about a failed GitHub API query.
    
    Parameters
    ----------
    error: BadRequest | QueryError
        The error that was raised by the GitHub API.
    faulty_frame: inspect.FrameInfo
        The frame in which the error was raised.
    additional_info: dict[str, int | str | bool] | str | None
        Additional information to be included in the error message.
    """

    def __init__(self, error: BadRequest | QueryError, faulty_frame: inspect.FrameInfo,
                 additional_info: tuple[str, dict[str, int | str | bool]] | str | None = None):
        self.error: BadRequest | QueryError = error
        self.faulty_frame: inspect.FrameInfo = faulty_frame
        self.filename: str = faulty_frame.filename
        self.lineno: int = faulty_frame.lineno
        self.function: str = faulty_frame.function
        self._additional_info: dict[str, int | str | bool] | str | None = additional_info

    @property
    def additional_info(self) -> str | None:
        if self._additional_info is None:
            return None
        if isinstance(self._additional_info, tuple):
            return f'GraphQL query "{self._additional_info[0]}" failed with the following variables:\n' \
                   f'{" ".join([f"{key}={value};" for key, value in self._additional_info[1].items()])}'
        return f'REST query path: {self._additional_info}'  # additional info is from a rest call

    @property
    def status_code(self) -> int | None:
        return self.error.status_code if hasattr(self.error, 'status_code') else None

    @property
    def matching_ignore_rules(self) -> list[str]:
        """
        Returns a list of ignorable error substrings that match the error message.
        If the list is non-empty, the error is ignorable.

        :return: A list of ignorable error substrings/rules that match the error message.
        """
        return [substring for substring in self.__ignorable_error_substrings__ if
                substring.casefold() in str(self.error).casefold()]

    @property
    def is_ignorable(self) -> bool:
        return bool(self.matching_ignore_rules)

    @property
    def code_location(self) -> str:
        return f'{self.filename}:#{self.lineno}:{self.function}()'

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} error={self.error} ignorable={self.is_ignorable} code_location="{self.code_location}">'


class GitHubAPI:
    __base_url__: str = 'https://api.github.com'
    __non_query_methods__: tuple[str, ...] = ('query', '_sanitize_graphql_variables')
    github_object_cache: TypedCache = TypedCache(CacheSchema(key=str, value=(dict, list)), maxsize=64, max_age=450)

    """
    The main class used to interact with the GitHub API.
    This is used both by the bot acting on its behalf as well as on behalf of the authorized users.

    Parameters
    ----------
    token: list
        The GitHub access token to send requests with.
    requester: str
        A :class:`str` denoting the author of the requests (ex. 'BigNoob420')
    """

    def __init__(self, bot: 'GitBot', token: str, session: aiohttp.ClientSession, requester: str = 'gitbot by statch'):
        requester += '; Python {v.major}.{v.minor}.{v.micro}'.format(v=version_info)
        self.bot: 'GitBot' = bot
        self.requester: str = requester
        self.__token: str = token
        self.queries: DirProxy = DirProxy('./resources/queries/', ('.gql', '.graphql'))
        self.session: aiohttp.ClientSession = session
        self.gh: gh.GitHubAPI = gh.GitHubAPI(session=self.session, requester=self.requester, oauth_token=self.__token)

    @staticmethod
    def _sanitize_graphql_variables(variables: dict[str, ...]) -> dict[str, ...]:
        """
        Sanitizes the variables dict passed to a GraphQL query. Add any sanitization logic here.

        :param variables: The variables dict to sanitize
        :return: The sanitized variables dict
        """
        if repo := variables.get(
                '_Repo'):  # _Repo is a special variable that is used to pass the repo name and owner at once
            variables['Owner'], variables['Name'] = repo.split('/') if repo.count('/') == 1 else (repo, repo)
            del variables['_Repo']
        return variables

    async def query(self,
                    query_or_path: str,
                    transformer: tuple[LiteralString, ...] | str | Callable[[dict], dict] | None = None,
                    on_fail_return: _GitHubAPIQueryWrapOnFailReturnDefaultConditionDict |
                                    _GitHubAPIQueryWrapOnFailReturnDefaultNotSet | bool | list | None = 'default_not_set',
                    **graphql_variables) -> _ReturnDict | list[_ReturnDict] | str | None:
        """
        Wraps a GitHub API query call, handling errors and returning the result.
        The request method is chosen between REST and GraphQL based on the query_or_path parameter -
        if it starts with a slash, REST is used, otherwise GraphQL is used.

        :param query_or_path: The meat and potatoes of the query. Can be either a path if REST is used, or a query if GraphQL is used.
        :param transformer: A transformer to apply to the result. Can be a callable, a tuple of strings or a string.
        :param on_fail_return: What to return if the query fails. If set to 'default_not_set', the query will raise an exception.
               A dict can be passed to specify conditional matching of returns, where the content of the API errors response
               is matched against the dict keys and the value of the matched key is returned.
        :param graphql_variables: The variables to pass to the GraphQL query if GraphQL is used.
        :return: The result of the query, or the result of the transformer if one was provided.
        """
        is_graphql: bool = not query_or_path.startswith('/')
        try:
            q_res: _ReturnDict = (
                await (self.gh.getitem(query_or_path) if not is_graphql else self.gh.graphql(query_or_path,
                                                                                             **self._sanitize_graphql_variables(
                                                                                                 graphql_variables))))
            transformer = (transformer,) if isinstance(transformer, str) and transformer is not None else transformer
            if isinstance(transformer, tuple):
                return get_nested_key(q_res, transformer)
            return transformer(q_res) if callable(transformer) else q_res
        except (QueryError, BadRequest) as e:
            e: BadRequest | QueryError  # idk why pycharm doesn't pick the types up on its own
            # below we get the frame of the function from this class that this very function was called from.
            # we cannot simply get the last one or anything, because of decorators getting in the way.
            # we make some expensive calls here, but it's fine because this is only called on errors
            actual_f_frame: inspect.FrameInfo = [frame for frame in inspect.stack() if frame.function in dir(self) and (
                    frame.function not in self.__non_query_methods__)][0]
            debug: GitHubQueryDebugInfo = GitHubQueryDebugInfo(e, actual_f_frame, (
                f'{[q_name for q_name, q_content in self.queries.__dict__.items() if q_content == query_or_path][0]}.graphql',
                graphql_variables) if is_graphql else query_or_path if is_graphql else query_or_path)
            if debug.is_ignorable and on_fail_return != 'default_not_set':
                self.bot.logger.debug(f'Ignoring GitHub {e.__class__.__name__} in query call {self.__class__.__name__}'
                                      f'.{actual_f_frame.function}(): "{e}" -> ignore conditions matched: {debug.matching_ignore_rules}')
                # {condition: return_value, __default__?: return_value}
                if isinstance(on_fail_return, dict):
                    for cond, ret in on_fail_return.items():
                        if cond in str(e):
                            return ret
                    return on_fail_return.get('__default__')
                return on_fail_return
            self.bot.logger.error(
                f'GitHub {e.__class__.__name__} in query call {self.__class__.__name__}.{actual_f_frame.function}: "{e}"')
            # we need to create a fake context to pass to the error logger; jank and probs needs rework in the future,
            # but it works just fine for now
            moot_context = type('_ctx', (object,), {'command': None, 'message': None, 'bot': self.bot,
                                                    'guild': self.bot.statch_guild,
                                                    'channel': self.bot.error_log_channel,
                                                    'gh_query_debug': debug})
            await log_error_in_discord(moot_context, e)  # noqa, we don't care that the context isn't real,
            # we only care that it has the properties we need
            raise e

    @_wrap_proxy
    async def get_ratelimit(self) -> _ReturnDict:
        return await self.query('/rate_limit')

    async def me(self) -> _ReturnDict:
        return await self.query('/user')

    @github_cached
    @validate_github_name('user')
    async def get_user_repos(self, user: GitHubUser) -> list[_ReturnDict]:
        return await self.query(f'/users/{user}/repos', on_fail_return=[])

    @github_cached
    @validate_github_name('org')
    async def get_org(self, org: GitHubOrganization) -> Optional[_ReturnDict]:
        return await self.query(f'/orgs/{org}', on_fail_return=None)

    @github_cached
    @validate_github_name('org', default=[])
    async def get_org_repos(self, org: GitHubOrganization) -> list[_ReturnDict]:
        return await self.query(f'/orgs/{org}/repos', on_fail_return=[])

    @normalize_repository
    async def get_tree_file(self, repo: GitHubRepository, path: str | None = None,
                            ref: str | None = None) -> _ReturnDict | list[_ReturnDict] | None:
        if repo.count('/') != 1:
            return None
        if path:
            if path[0] != '/':
                path = '/' + path
        else:
            path = ''
        return await self.query(f'/repos/{repo}/contents{path}' + (f'?ref={ref}' if ref else ''), on_fail_return=None)

    @github_cached
    @validate_github_name('user', default=[])
    async def get_user_orgs(self, user: GitHubUser) -> list[_ReturnDict]:
        return await self.query(f'/users/{user}/orgs', on_fail_return=[])

    @github_cached
    @validate_github_name('org', default=[])
    async def get_org_members(self, org: GitHubOrganization) -> list[_ReturnDict]:
        return await self.query(f'/orgs/{org}/public_members', on_fail_return=[])

    @github_cached
    async def get_gist(self, gist_id: str) -> Optional[_ReturnDict]:
        return await self.query(f'/gists/{gist_id}', on_fail_return=None)

    @_wrap_proxy
    @github_cached
    @validate_github_name('user')
    async def get_user_gists(self, user: GitHubUser) -> Optional[_ReturnDict]:
        return await self.query(self.queries.user_gists, 'user', Login=user, on_fail_return=None)

    @_wrap_proxy
    @normalize_repository
    async def get_latest_commit(self, repo: GitHubRepository) -> Optional[_ReturnDict] | Literal[False]:
        return await self.query(self.queries.latest_commit, on_fail_return={'Repository': False, '__default__': None},
                                transformer=('repository', 'defaultBranchRef', 'target'), _Repo=repo)

    @_wrap_proxy
    @normalize_repository
    async def get_commit(self, repo: GitHubRepository, oid: str) -> Optional[_ReturnDict] | Literal[False]:
        return await self.query(self.queries.commit, on_fail_return={'Repository': False, '__default__': None},
                                _Repo=repo, Oid=oid, transformer=('repository', 'object'))

    @_wrap_proxy
    @normalize_repository
    async def get_latest_commits(self, repo: GitHubRepository, ref: Optional[str] = None) -> list[_ReturnDict] | str:
        try:
            key: str = 'defaultBranchRef'
            if not ref:
                data = await self.query(self.queries.latest_commits_from_default_ref,
                                        on_fail_return={'Repository': 'repo', '__default__': 'ref'},
                                        _Repo=repo, First=10)
            else:
                key: str = 'ref'
                data = await self.query(self.queries.latest_commits_from_ref,
                                        on_fail_return={'Repository': 'repo', '__default__': 'ref'},
                                        _Repo=repo, First=10, RefName=ref)
        except QueryError as e:
            if 'Repository' in str(e):
                return 'repo'
            return 'ref'
        if 'defaultBranchRef' not in data.get('repository', {}) and 'ref' not in data['repository']:
            return 'ref'
        try:
            return data['repository'][key]['target']['history']['nodes']
        except (TypeError, KeyError):
            return []

    @normalize_repository
    async def get_repo_zip(self,
                           repo: GitHubRepository,
                           size_threshold: int = DISCORD_UPLOAD_SIZE_THRESHOLD_BYTES) -> Optional[bool | bytes]:
        if '/' not in repo or repo.count('/') > 1:
            return None
        res = await self.session.get(self.__base_url__ + f'/repos/{repo}/zipball',
                                     headers={'Authorization': f'token {self.__token}'})
        if res.status == 200:
            try:
                await res.content.readexactly(size_threshold)
            except asyncio.IncompleteReadError as read:
                return read.partial
            else:
                return False
        return None

    @_wrap_proxy
    @normalize_repository
    async def get_latest_release(self, repo: GitHubRepository) -> Optional[_ReturnDict]:
        return await self.query(self.queries.latest_release, _Repo=repo, transformer=transform_latest_release, on_fail_return=None)

    @_wrap_proxy
    @normalize_repository
    @github_cached
    async def get_repo(self, repo: GitHubRepository) -> Optional[_ReturnDict]:
        return await self.query(self.queries.repo, transformer=transform_repo, on_fail_return=None, _Repo=repo)

    @_wrap_proxy
    @normalize_repository
    @github_cached
    async def rest_get_repo(self, repo: GitHubRepository) -> Optional[_ReturnDict]:
        return await self.query(f'/repos/{repo}', on_fail_return=None)

    @_wrap_proxy
    @normalize_repository
    async def get_pull_request(self,
                               repo: GitHubRepository,
                               number: int,
                               data: Optional[dict] = None) -> _ReturnDict | str:
        if not data:
            return await self.query(self.queries.pull_request, _Repo=repo, Number=number,
                                    on_fail_return={'number': 'number', '__default__': 'repo'},
                                    transformer=transform_pull_request)
        return transform_pull_request(data)

    @_wrap_proxy
    @normalize_repository
    async def get_last_pull_requests_by_state(self,
                                              repo: GitHubRepository,
                                              last: int = 10,
                                              state: str = 'OPEN') -> Optional[list[_ReturnDict]]:
        return await self.query(self.queries.pull_requests, _Repo=repo, Last=last, States=state,
                                on_fail_return=None, transformer=('repository', 'pullRequests', 'nodes'))

    @_wrap_proxy
    @_flatten_total_counts
    @normalize_repository
    async def get_issue(self,
                        repo: GitHubRepository,
                        number: int,
                        data: Optional[dict] = None,  # If data isn't None, this method simply acts as a parser
                        had_keys_removed: bool = False) -> _ReturnDict | str:
        if not data:
            return await self.query(self.queries.issue, _Repo=repo, Number=number,
                                    on_fail_return={'number': 'number', '__default__': 'repo'},
                                    transformer=transform_issue)
        if isinstance(data, dict):
            return transform_issue(data, had_keys_removed)

    @_wrap_proxy
    @normalize_repository
    async def get_last_issues_by_state(self,
                                       repo: GitHubRepository,
                                       last: int = 10,
                                       state: str = 'OPEN') -> Optional[list[_ReturnDict]]:
        return await self.query(self.queries.issues, _Repo=repo, Last=last, States=state,
                                transformer=('repository', 'issues', 'nodes'), on_fail_return=None)

    @_wrap_proxy
    @_flatten_total_counts
    @github_cached
    @validate_github_name('user')
    async def get_user(self, user: GitHubUser) -> Optional[_ReturnDict]:
        return await self.query(self.queries.user, Login=user, FromTime=YEAR_START,
                                ToTime=datetime.utcnow().strftime('%Y-%m-%dT%XZ'),
                                on_fail_return=None, transformer=transform_user)
