from os import getenv
from dotenv import load_dotenv
from core.github.api import GitHubAPI

load_dotenv()

Git = GitHubAPI((getenv('GITHUB'), getenv('GITHUB_WORKER')), 'itsmewulf')
