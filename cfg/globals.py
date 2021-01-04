from os import getenv
from dotenv import load_dotenv
from core.api import API

load_dotenv()

Git = API(getenv('GITHUB'))
