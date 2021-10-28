from os import getenv
from dotenv import load_dotenv
from lib.api.github import GitHubAPI
from lib.api.carbonara import Carbon as _Carbon
from lib.api.pypi import PyPIAPI
from lib.manager import Manager

__all__: tuple = ('Git', 'Mgr', 'Carbon', 'PyPI')

load_dotenv()

Git: GitHubAPI = GitHubAPI((getenv('GITHUB_MAIN'), getenv('GITHUB_SECONDARY')), 'gitbot')
Mgr: Manager = Manager(Git)
Carbon: _Carbon = _Carbon(Git.ses)
PyPI: PyPIAPI = PyPIAPI(Git.ses)
