import re

REPO_RE = re.compile(r"https://github\.com/([a-zA-Z0-9-_]+/[A-Za-z0-9_.-]+)")
USER_ORG_RE = re.compile(r"https://github\.com/([a-zA-Z0-9-_]+)")
PR_RE = re.compile(r"https://github\.com/([a-zA-Z0-9-_]+/[A-Za-z0-9_.-]+)/pull/(\d+)")
ISSUE_RE = re.compile(
    r"https://github\.com/([a-zA-Z0-9-_]+/[A-Za-z0-9_.-]+)/issues/(\d+)"
)
MD_EMOJI_RE = re.compile(r":.*:", re.IGNORECASE)

GITHUB_LINES_RE = re.compile(
    r"github\.com/([a-zA-Z0-9-_]+/[A-Za-z0-9_.-]+)/blob/(.+?)/(.+?)#L(\d+)[-~]?L?(\d*)"
)
GITLAB_LINES_RE = re.compile(
    r"gitlab\.com/([a-zA-Z0-9-_]+/[A-Za-z0-9_.-]+)/-/blob/(.+?)/(.+?)#L(\d+)-?(\d*)"
)
