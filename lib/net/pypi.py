import aiohttp
from typing import Optional

BASE_URL: str = 'https://pypi.org/pypi'


class PyPIAPI:
    def __init__(self, ses: aiohttp.ClientSession = aiohttp.ClientSession()):
        self.ses: aiohttp.ClientSession = ses

    async def get_project_data(self, project: str) -> Optional[dict]:
        res: aiohttp.ClientResponse = await self.ses.get(BASE_URL + f'/{project}/json')
        if res.status == 200:
            return await res.json()

    async def get_project_version_data(self, project: str, version: str) -> Optional[dict]:
        # This endpoint doesn't make sense, returns the same data as the non-versioned one
        res: aiohttp.ClientResponse = await self.ses.get(BASE_URL + f'/{project}/{version}/json')
        if res.status == 200:
            return await res.json()

    async def get_project_recent_downloads(self, project: str):
        res: aiohttp.ClientResponse = await self.ses.get(f'https://pypistats.org/api/packages/{project.lower()}/recent')
        if res.status == 200:
            return await res.json()
