import aiohttp
from typing import Optional

BASE_URL_PYPI: str = 'https://pypi.org/pypi'
BASE_URL_PYPISTATS: str = 'https://pypistats.org/api'


class PyPIAPI:
    def __init__(self, ses: aiohttp.ClientSession):
        self.ses: aiohttp.ClientSession = ses

    async def get_project_data(self, project: str) -> Optional[dict]:
        res: aiohttp.ClientResponse = await self.ses.get(BASE_URL_PYPI + f'/{project}/json')
        if res.status == 200:
            return await res.json()

    async def get_project_version_data(self, project: str, version: str) -> Optional[dict]:
        # This endpoint doesn't make sense, returns the same data as the non-versioned one
        res: aiohttp.ClientResponse = await self.ses.get(BASE_URL_PYPI + f'/{project}/{version}/json')
        if res.status == 200:
            return await res.json()

    async def get_project_overall_downloads(self, project: str, mirrors: bool = False) -> Optional[dict]:
        res: aiohttp.ClientResponse = await self.ses.get(BASE_URL_PYPISTATS + f'/packages/{project.lower()}/overall?mirrors={str(mirrors).lower()}')
        if res.status == 200:
            return await res.json()

    async def get_project_recent_downloads(self, project: str) -> Optional[dict]:
        res: aiohttp.ClientResponse = await self.ses.get(BASE_URL_PYPISTATS + f'/packages/{project.lower()}/recent')
        if res.status == 200:
            return await res.json()
