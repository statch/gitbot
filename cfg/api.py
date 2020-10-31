from os import getenv
from github import Github
from dotenv import load_dotenv


class Instance:
    """Main Class used to interact with the GitHub API"""

    # TODO Apply for GitHub Developer Program to get bigger rate limits
    def __init__(self):
        load_dotenv()
        self.user = Github(getenv("GITHUB"))
