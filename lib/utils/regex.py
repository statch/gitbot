import re

REPO_RE: re.Pattern = re.compile(r'https://github\.com/([a-zA-Z0-9-_]+/[A-Za-z0-9_.-]+)', re.IGNORECASE)
USER_ORG_RE: re.Pattern = re.compile(r'https://github\.com/([a-zA-Z0-9-_]+)', re.IGNORECASE)
PR_RE: re.Pattern = re.compile(r'https://github\.com/([a-zA-Z0-9-_]+/[A-Za-z0-9_.-]+)/pull/(\d+)', re.IGNORECASE)
ISSUE_RE: re.Pattern = re.compile(r'https://github\.com/([a-zA-Z0-9-_]+/[A-Za-z0-9_.-]+)/issues/(\d+)', re.IGNORECASE)
MD_EMOJI_RE: re.Pattern = re.compile(r':.*:', re.IGNORECASE)
CODEBLOCK_RE: re.Pattern = re.compile(r'``?`?([a-z]*\n.+\n)*.+``?`?')
ANY_URL_RE: re.Pattern = re.compile(
    r'https?://(www\.)?[a-zA-Z0-9@:%._+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_+.~#?&/=]*)', re.IGNORECASE)
GITHUB_LINES_RE: re.Pattern = re.compile(
    r'(github)\.com/([a-zA-Z0-9-_]+/[A-Za-z0-9_.-]+)/blob/(.+?)/(.+?)#L(\d+)[-~]?L?(\d*)', re.IGNORECASE)
GITLAB_LINES_RE: re.Pattern = re.compile(
    r'(gitlab)\.com/([a-zA-Z0-9-_]+/[A-Za-z0-9_.-]+)/-/blob/(.+?)/(.+?)#L(\d+)-?(\d*)', re.IGNORECASE)
GITHUB_REPO_URL: re.Pattern = re.compile(
    r'github\.com/([a-zA-Z0-9-_]+)/([A-Za-z0-9_.-]+)'
)
GITHUB_REPO_GIT_URL: re.Pattern = re.compile(
    r'github\.com/([a-zA-Z0-9-_]+)/([A-Za-z0-9_.-]+)\.git'
)
