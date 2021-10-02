import re

REPO_RE: re.Pattern = re.compile(r'https://github\.com/(?P<repo>[a-zA-Z0-9-_]+/[A-Za-z0-9_.-]+)', re.IGNORECASE)
PASCAL_CASE_NAME_RE: re.Pattern = re.compile(r'(?<!^)(?=[A-Z])')
USER_ORG_RE: re.Pattern = re.compile(r'https://github\.com/(?P<name>[a-zA-Z0-9-_]+)', re.IGNORECASE)
PR_RE: re.Pattern = re.compile(r'https://github\.com/(?P<repo>[a-zA-Z0-9-_]+/[A-Za-z0-9_.-]+)/pull/(?P<number>\d+)', re.IGNORECASE)
PULLS_PLAIN_RE: re.Pattern = re.compile(r'https://github\.com/(?P<repo>[a-zA-Z0-9-_]+/[A-Za-z0-9_.-]+)/pulls', re.IGNORECASE)
ISSUE_RE: re.Pattern = re.compile(r'https://github\.com/(?P<repo>[a-zA-Z0-9-_]+/[A-Za-z0-9_.-]+)/issues/(?P<number>\d+)', re.IGNORECASE)
ISSUES_PLAIN_RE: re.Pattern = re.compile(r'https://github\.com/(?P<repo>[a-zA-Z0-9-_]+/[A-Za-z0-9_.-]+)/issues', re.IGNORECASE)
MD_EMOJI_RE: re.Pattern = re.compile(r'<?:.*:([0-9]{18})?>?', re.IGNORECASE)
MULTILINE_CODEBLOCK_RE: re.Pattern = re.compile(r'```(?P<extension>[a-z]*)\n*(?P<content>[\s\S]+)\n*```')
SINGLE_LINE_CODEBLOCK_RE: re.Pattern = re.compile(r'`(?P<content>[\s\S]+)`')
GITHUB_REPO_GIT_URL: re.Pattern = re.compile(r'github\.com/(?P<repo>[a-zA-Z0-9-_]+)/([A-Za-z0-9_.-]+)\.git', re.IGNORECASE)
LOCALE_EMOJI: re.Pattern = re.compile(r'{emoji_(?P<emoji_name>[a-zA-Z-_]+)}', re.IGNORECASE)
GITHUB_LINES_RE: re.Pattern = re.compile(
    r'(github)\.com/(?P<repo>[a-zA-Z0-9-_]+/[A-Za-z0-9_.-]+)/blob/(.+?)/(.+?)#L(\d+)[-~]?L?(\d*)', re.IGNORECASE)
GITLAB_LINES_RE: re.Pattern = re.compile(
    r'(gitlab)\.com/(?P<repo>[a-zA-Z0-9-_]+/[A-Za-z0-9_.-]+)/-/blob/(.+?)/(.+?)#L(\d+)-?(\d*)', re.IGNORECASE)
GITHUB_NAME_RE: re.Pattern = re.compile(r'^[a-z\d](?:[a-z\d]|-(?=[a-z\d])){0,38}$', re.IGNORECASE)
GIT_OBJECT_ID_RE: re.Pattern = re.compile(r'\b([a-f0-9]{40})\b')
