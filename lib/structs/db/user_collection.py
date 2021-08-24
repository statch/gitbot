from motor.motor_asyncio import AsyncIOMotorCollection
from typing import Optional
from lib.utils.decorators import normalize_identity
from lib.typehints import Identity


class UserCollection(AsyncIOMotorCollection):
    """A wrapper around :class:`AsyncIOMotorCollection` adding methods for simple attribute access and modification.

    Parameters
    ----------
    collection: :class:`AsyncIOMotorCollection`
        The collection to add methods to.

    github: :class:`core.net.github.api.GitHubAPI`
        The GitHub API instance for validating inserts

    mgr: :class:`lib.manager.Manager`
        The Manager instance for validating inserts
    """

    def __init__(self, collection: AsyncIOMotorCollection, github, mgr):
        self._git = github
        self._mgr = mgr
        super().__init__(collection.database, collection.name)

    @normalize_identity
    async def delitem(self, _id: Identity, field: str) -> bool:
        query: dict = await self.find_one({"_id": _id})
        if query is not None and field in query:
            await self.update_one(query, {"$unset": {field: ""}})
            del query[field]
            if len(query) == 1:
                await self.find_one_and_delete({"_id": _id})
            return True
        return False

    @normalize_identity
    async def getitem(self, _id: Identity, item: str) -> Optional[str]:
        query: dict = await self.find_one({'_id': _id})
        if query and item in query:
            return query[item]
        return None

    @normalize_identity
    async def setitem(self, _id: Identity, item: str, value: str) -> bool:
        valid: bool = True
        if item in ('user', 'repo', 'org'):
            valid: bool = await ({'user': self._git.get_user, 'repo': self._git.get_repo, 'org': self._git.get_org}[item])(value) is not None
        elif item == 'locale':
            valid: bool = any([l_['name'] == value for l_ in self._mgr.locale.languages])
        if valid:
            query = await self.find_one({"_id": _id})
            if query is not None:
                await self.update_one(query, {"$set": {item: value}})
            else:
                await self.insert_one({"_id": _id, item: value})
            return True
        return False

