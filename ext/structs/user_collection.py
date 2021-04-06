from motor.motor_asyncio import AsyncIOMotorCollection
from discord.ext import commands
from typing import Optional


class UserCollection(AsyncIOMotorCollection):
    """A wrapper around :class:`AsyncIOMotorCollection` adding methods for simple attribute access and modification.

    Parameters
    ----------
    collection: :class:`AsyncIOMotorCollection`
        The collection to add methods to.

    github: :class:`core.net.github.api.GitHubAPI`
        The GitHub API instance for validating inserts.
    """

    def __init__(self, collection: AsyncIOMotorCollection, github):
        self._git = github
        super().__init__(collection.database, collection.name)

    async def delitem(self, ctx: commands.Context, field: str) -> bool:
        query: dict = await self.find_one({"_id": ctx.author.id})
        if query is not None and field in query:
            await self.update_one(query, {"$unset": {field: ""}})
            del query[field]
            if len(query) == 1:
                await self.find_one_and_delete({"_id": ctx.author.id})
            return True
        return False

    async def getitem(self, ctx: commands.Context, item: str) -> Optional[str]:
        query: dict = await self.find_one({'_id': ctx.author.id})
        if query and item in query:
            return query[item]
        return None

    async def setitem(self, ctx: commands.Context, item: str, value: str) -> bool:
        exists: bool = True
        if item in ('user', 'repo', 'org'):
            exists: bool = await ({'user': self._git.get_user, 'repo': self._git.get_repo, 'org': self._git.get_org}[item])(value) is not None
        if exists:
            query = await self.find_one({"_id": ctx.author.id})
            if query is not None:
                await self.update_one(query, {"$set": {item: value}})
            else:
                await self.insert_one({"_id": ctx.author.id, item: value})
            return True
        return False

