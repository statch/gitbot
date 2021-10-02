from os import getenv
from dotenv import load_dotenv
from lib.net.github.api import GitHubAPI
from lib.manager import Manager
from lib.net.carbonara import Carbon as _Carbon
from lib.net.pypi import PyPIAPI

__all__: tuple = ('Git', 'Mgr', 'Carbon', 'PyPI')

load_dotenv()

Git: GitHubAPI = GitHubAPI((getenv('GITHUB_MAIN'), getenv('GITHUB_SECONDARY')), 'itsmewulf')
Mgr: Manager = Manager(Git)
Carbon: _Carbon = _Carbon(Git.ses)
PyPI: PyPIAPI = PyPIAPI(Git.ses)
