import re

# For URLs, use "(?:https?://)?" for protocol prefixes since we don't really care about them

HELP_PARAMETER_REGEX = re.compile(r'(?P<param_type>[\[<])(?P<param_name>[a-zA-Z-_]+)[]>]')
GIT_OBJECT_ID_RE: re.Pattern = re.compile(r'\b([a-f0-9]{40})\b')
MARKDOWN_EMOJI_RE: re.Pattern = re.compile(r'<?:.*:([0-9]{18})?>?', re.IGNORECASE)
LOCALE_EMOJI_TEMPLATE_RE: re.Pattern = re.compile(r'{emoji_(?P<emoji_name>[a-zA-Z-_]+)}', re.IGNORECASE)
DISCORD_CHANNEL_MENTION_RE: re.Pattern = re.compile(r'<#(?P<id>\d{18})>')
MULTILINE_CODEBLOCK_RE: re.Pattern = re.compile(r'```(?P<extension>[a-z]*)\n*(?P<content>[\s\S]+)\n*```')
SINGLE_LINE_CODEBLOCK_RE: re.Pattern = re.compile(r'^`(?P<content>[\s\S]+)`$')
REPOSITORY_NAME_RE: re.Pattern = re.compile(r'(?P<slashname>(?P<owner>[a-z\d](?:[a-z\d]|-(?=[a-z\d])){0,38})/(?P<name>[a-z\d.](?:[a-z\d.]|-(?=[a-z\d.])){0,38}))/?(?P<branch>[a-z\d.](?:[a-z\d.]|-(?=[a-z\d.])){0,38})?', re.IGNORECASE)

GITHUB_NAME_RE: re.Pattern = re.compile(r'^[a-z\d](?:[a-z\d]|-(?=[a-z\d])){0,38}$', re.IGNORECASE)
GITHUB_REPO_URL_RE: re.Pattern = re.compile(r'(?:https?://)?github\.com/(?P<repo>[a-z\d](?:[a-z\d]|-(?=[a-z\d])){0,38}/[a-z\d.](?:[a-z\d.]|-(?=[a-z\d.])){0,38})', re.IGNORECASE)
GITHUB_USER_ORG_URL_RE: re.Pattern = re.compile(r'(?:https?://)?github\.com/(?P<name>[a-z\d](?:[a-z\d]|-(?=[a-z\d])){0,38})', re.IGNORECASE)
GITHUB_PULL_REQUEST_URL_RE: re.Pattern = re.compile(r'(?:https?://)?github\.com/(?P<repo>[a-zA-Z0-9-_]+/[A-Za-z0-9_.-]+)/pull/(?P<number>\d+)', re.IGNORECASE)
GITHUB_PULL_REQUESTS_PLAIN_URL_RE: re.Pattern = re.compile(r'(?:https?://)?github\.com/(?P<repo>[a-zA-Z0-9-_]+/[A-Za-z0-9_.-]+)/pulls', re.IGNORECASE)
GITHUB_ISSUE_URL_RE: re.Pattern = re.compile(r'(?:https?://)?github\.com/(?P<repo>[a-zA-Z0-9-_]+/[A-Za-z0-9_.-]+)/issues/(?P<number>\d+)', re.IGNORECASE)
GITHUB_ISSUES_PLAIN_URL_RE: re.Pattern = re.compile(r'(?:https?://)?github\.com/(?P<repo>[a-zA-Z0-9-_]+/[A-Za-z0-9_.-]+)/issues', re.IGNORECASE)
GITHUB_REPO_GIT_URL_RE: re.Pattern = re.compile(r'(?:https?://)?github\.com/(?P<repo>[a-zA-Z0-9-_]+/[A-Za-z0-9_.-]+)\.git', re.IGNORECASE)
GITHUB_LINES_URL_RE: re.Pattern = re.compile(r'(?:https?://)?(github)\.com/(?P<repo>[a-zA-Z0-9-_]+/[A-Za-z0-9_.-]+)/blob/(.+?)/(.+?)#L(?P<first_line_number>\d+)[-~]?L?(?P<second_line_number>\d*)', re.IGNORECASE)
GITLAB_LINES_URL_RE: re.Pattern = re.compile(r'(?:https?://)?(gitlab)\.com/(?P<repo>[a-zA-Z0-9-_]+/[A-Za-z0-9_.-]+)/-/blob/(.+?)/(.+?)#L(?P<first_line_number>\d+)-?(?P<second_line_number>\d*)', re.IGNORECASE)
GITHUB_COMMIT_URL_RE: re.Pattern = re.compile(r'(?:https?://)?github\.com/(?P<repo>[a-zA-Z0-9-_]+/[A-Za-z0-9_.-]+)/commit/(?P<oid>\b([a-f0-9]{40})\b)')
