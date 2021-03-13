from os import getenv
from dotenv import load_dotenv
from core.net.github.api import GitHubAPI
from ext.manager import Manager

load_dotenv()

Git: GitHubAPI = GitHubAPI((getenv('GITHUB_MAIN'), getenv('GITHUB_SECONDARY')), 'itsmewulf')
Mgr: Manager = Manager(Git)
