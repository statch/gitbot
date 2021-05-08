from motor.motor_asyncio import AsyncIOMotorCollection
from discord.ext import commands
from typing import Optional
from ext.typehints import Identifiable


class UserCollection(AsyncIOMotorCollection):
    """A wrapper around :class:`AsyncIOMotorCollection` adding methods for simple attribute access and modification.

    Parameters
    ----------
    collection: :class:`AsyncIOMotorCollection`
        The collection to add methods to.

    github: :class:`core.net.github.api.GitHubAPI`
        The GitHub API instance for validating inserts

    mgr: :class:`ext.manager.Manager`
        The Manager instance for validating inserts
    """

    def __init__(self, collection: AsyncIOMotorCollection, github, mgr):
        self._git = github
        self._mgr = mgr
        super().__init__(collection.database, collection.name)

    async def delitem(self,  __id: Identifiable, field: str) -> bool:
        __id: int = __id if not isinstance(__id, commands.Context) else __id.author.id
        query: dict = await self.find_one({"_id": __id})
        if query is not None and field in query:
            await self.update_one(query, {"$unset": {field: ""}})
            del query[field]
            if len(query) == 1:
                await self.find_one_and_delete({"_id": __id})
            return True
        return False

    async def getitem(self, __id: Identifiable, item: str) -> Optional[str]:
        __id: int = __id if not isinstance(__id, commands.Context) else __id.author.id
        query: dict = await self.find_one({'_id': __id})
        if query and item in query:
            return query[item]
        return None

    async def setitem(self,  __id: Identifiable, item: str, value: str) -> bool:
        __id: int = __id if not isinstance(__id, commands.Context) else __id.author.id
        valid: bool = True
        if item in ('user', 'repo', 'org'):
            valid: bool = await ({'user': self._git.get_user, 'repo': self._git.get_repo, 'org': self._git.get_org}[item])(value) is not None
        elif item == 'locale':
            valid: bool = any([l_['name'] == value for l_ in self._mgr.locale.languages])
        if valid:
            query = await self.find_one({"_id": __id})
            if query is not None:
                await self.update_one(query, {"$set": {item: value}})
            else:
                await self.insert_one({"_id": __id, item: value})
            return True
        return False

