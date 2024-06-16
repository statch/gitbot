# coding: utf-8

from typing import TypeVar
from lib.structs import (DictProxy, SnakeCaseDictProxy, CaseInsensitiveSnakeCaseDict,
                         CaseInsensitiveDict, CaseInsensitiveFixedSizeOrderedDict)

__all__: tuple = ('transform_pull_request', 'transform_repo', 'transform_latest_release', 'transform_user', 'transform_issue')
_Transformable = TypeVar('_Transformable', DictProxy, SnakeCaseDictProxy, CaseInsensitiveSnakeCaseDict,
                         CaseInsensitiveDict, CaseInsensitiveFixedSizeOrderedDict, dict)


def transform_pull_request(pull_request_dict: _Transformable) -> _Transformable:
    pull_request_dict: dict = pull_request_dict['repository'][
        'pullRequest'] if 'repository' in pull_request_dict else pull_request_dict
    pull_request_dict['labels']: list = [lb['node']['name'] for lb in pull_request_dict['labels']['edges']]
    pull_request_dict['assignees']['users'] = [(u['node']['login'], u['node']['url']) for u in
                                               pull_request_dict['assignees']['edges']]
    pull_request_dict['reviewers'] = {}
    pull_request_dict['reviewers']['users'] = [
        (o['node']['requestedReviewer']['login'] if 'login' in o['node']['requestedReviewer'] else
         o['node']['requestedReviewer']['name'], o['node']['requestedReviewer']['url']) for o
        in pull_request_dict['reviewRequests']['edges']]
    pull_request_dict['reviewers']['totalCount'] = pull_request_dict['reviewRequests']['totalCount']
    pull_request_dict['participants']['users'] = [(u['node']['login'], u['node']['url']) for u in
                                                  pull_request_dict['participants']['edges']]
    return pull_request_dict


def transform_repo(repo_dict: _Transformable) -> _Transformable:
    repo_dict = repo_dict['repository']
    repo_dict['languages'] = repo_dict['languages']['totalCount']
    repo_dict['topics'] = (repo_dict['repositoryTopics']['nodes'], repo_dict['repositoryTopics']['totalCount'])
    repo_dict['graphic'] = repo_dict['openGraphImageUrl'] if repo_dict['usesCustomOpenGraphImage'] else None
    repo_dict['release'] = repo_dict['releases']['nodes'][0]['tagName'] if repo_dict['releases']['nodes'] else None
    return repo_dict


def transform_latest_release(release_dict: _Transformable) -> _Transformable:
    release_dict = release_dict['repository']
    release_dict['release'] = release_dict['latestRelease'] if release_dict.get('latestRelease') else None  # .get for parity with backlog fetching
    release_dict['color'] = int(release_dict['primaryLanguage']['color'][1:], 16) if release_dict[
        'primaryLanguage'] else 0x2f3136
    try:   # parity with backlog fetching
        del release_dict['primaryLanguage']
        del release_dict['latestRelease']
    except KeyError:
        pass
    return release_dict


def transform_user(user_dict: _Transformable) -> _Transformable:
    user_dict_ = user_dict['user']['contributionsCollection']['contributionCalendar']
    user_dict['user']['contributions'] = user_dict_['totalContributions'], \
        user_dict_['weeks'][-1]['contributionDays'][-1][
            'contributionCount']
    user_dict = user_dict['user']
    del user_dict['contributionsCollection']
    return user_dict


def transform_issue(issue_dict: _Transformable, had_keys_removed: bool = False) -> _Transformable:
    if not had_keys_removed:
        issue_dict: dict = issue_dict['repository']['issue']
    issue_dict['body']: str = issue_dict['bodyText']
    del issue_dict['bodyText']
    issue_dict['labels']: list = [lb['name'] for lb in list(issue_dict['labels']['nodes'])]
    return issue_dict
