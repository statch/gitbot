# coding: utf-8

from typing import Optional
from lib.utils.decorators import normalize_identity
from typing import TYPE_CHECKING, Iterable
from lib.structs.db.collections.collection_wrapper import CollectionWrapper
from lib.utils.dict_utils import get_nested_key
from lib.typehints import Identity, LocaleName
from lib.structs import DictProxy

if TYPE_CHECKING:
    from lib.structs.db.database_proxy import DatabaseProxy


__all__: tuple = ('UsersCollection',)


class UsersCollection(CollectionWrapper):
    __wrapped_collection_name__: str = 'users'

    """
    A wrapper around :class:`AsyncIOMotorCollection` adding methods to the users collection.

    Parameters
    ----------
    collection: :class:`AsyncIOMotorCollection`
        The collection to add methods to.
    """

    def __init__(self, db: 'DatabaseProxy'):
        super().__init__(db, self.__wrapped_collection_name__)

    @normalize_identity()
    async def delitem(self, _id: Identity, field: str | Iterable[str]) -> bool:
        query: Optional[dict] = await self.find_one({'_id': _id})
        if query is not None and get_nested_key(query, field) is not None:
            await self.update_one(query, {'$unset': {field: ''}})
            return True
        return False

    @normalize_identity()
    async def getitem(self, _id: Identity, item: str | Iterable[str]) -> Optional[
        str | dict | list | bool | int | float]:
        query: Optional[dict] = await self.find_one({'_id': _id})
        if query and (ret := get_nested_key(query, item)) is not None:
            return ret
        return None

    @normalize_identity()
    async def setitem(self, _id: Identity, item: str, value: str | int | float | bool | dict | list,
                      validate: bool = True) -> bool:
        valid: bool = True
        if validate:
            if item in ('user', 'repo', 'org'):
                valid: bool = await (getattr(self.bot.github, f'get_{item}'))(value) is not None
            elif item == 'locale':
                valid: bool = any(l_['name'] == value for l_ in self._mgr.locale.languages)
        else:
            valid: bool = True
        if valid:
            query: Optional[dict] = await self.find_one({'_id': _id})
            if query is not None:
                await self.update_one(query, {'$set': {item: value}})
            else:
                await self.insert_one({'_id': _id, item: value})
            return True
        return False

    @normalize_identity()
    async def get_locale(self, _id: Identity) -> DictProxy:
        """
        Get the locale associated with a user, defaults to the master locale

        :param _id: The user object/ID to get the locale for
        :return: The locale associated with the user
        """
        locale: LocaleName = self.bot.mgr.locale.master.meta.name
        if cached := self.bot.get_cache_v('locale', _id):
            locale: LocaleName = cached
            self.bot.logger.debug('Returning cached locale for identity "%d"', _id)
        else:
            if stored := await self.getitem(_id, 'locale'):
                locale: str = stored
        try:
            self.bot.set_cache_v('locale', _id, locale)
            return getattr(self.bot.mgr.l, locale)
        except AttributeError:
            return self.bot.mgr.locale.master
