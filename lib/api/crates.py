# This isn't exactly a battle-tested, or even documented way of interacting with crates.io, but
# - it works
# - it's easy to use
# - it's not against their TOS
# "spec" @ https://github.com/rust-lang/crates.io/blob/c128a6765648d46a0e2246a669c994bfd494fef4/src/lib.rs#L73-L95


import aiohttp

BASE_URL_CRATES: str = 'https://crates.io/api/v1'


class CratesIOAPI:
    def __init__(self, ses: aiohttp.ClientSession):
        self.ses: aiohttp.ClientSession = ses

    async def get_crate_data(self, crate: str) -> dict | None:
        res: aiohttp.ClientResponse = await self.ses.get(BASE_URL_CRATES + f'/crates/{crate}')
        if res.status == 200:
            return await res.json()

    async def keyfetch_or_none(self,
                               endpoint: str,
                               key: str | list,
                               list_index: int | None = None) -> dict | list | str | int | bool | None:
        res: aiohttp.ClientResponse = await self.ses.get(BASE_URL_CRATES + endpoint)
        if res.status == 200:
            data: dict = await res.json()
            try:
                if isinstance(key, str):
                    data = data[key]
                else:
                    for k in key:
                        data = data[k]
                if list_index is not None and isinstance(data, list):
                    return data[list_index]
                return data
            except KeyError:
                return None

    async def get_crate_downloads(self, crate: str) -> list | None:
        return await self.keyfetch_or_none(f'/crates/{crate}/downloads', ['meta', 'extra_downloads'])

    async def get_crate_owners(self, crate: str) -> list | None:
        return await self.keyfetch_or_none(f'/crates/{crate}/owners', 'users')

    async def get_crate_owner_users(self, crate: str) -> list | None:
        return await self.keyfetch_or_none(f'/crates/{crate}/owner_user', 'users')

    async def get_crate_owner_teams(self, crate: str) -> list | None:
        return await self.keyfetch_or_none(f'/crates/{crate}/owner_team', 'teams')
