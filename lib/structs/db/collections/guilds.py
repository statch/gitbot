# coding: utf-8

from typing import Optional, Type
from lib.utils.decorators import normalize_identity
from typing import TYPE_CHECKING
from lib.structs.db.collections.collection_wrapper import CollectionWrapper
from lib.typehints import Identity, GitBotGuild, AutomaticConversionSettings

if TYPE_CHECKING:
    from lib.structs.db.database_proxy import DatabaseProxy

__all__: tuple = ('GuildsCollection',)


class GuildsCollection(CollectionWrapper):
    __wrapped_collection_name__: str = 'guilds'

    """
    A wrapper around :class:`AsyncIOMotorCollection` adding methods to the guilds collection.

    Parameters
    ----------
    collection: :class:`AsyncIOMotorCollection`
        The collection to add methods to.
    """

    def __init__(self, db: 'DatabaseProxy'):
        super().__init__(db, self.__wrapped_collection_name__)

    @normalize_identity(context_resource='guild')
    async def get_autoconv_config(self,
                                  _id: Identity,
                                  did_exist: bool = False) -> Type[AutomaticConversionSettings] | tuple[
        AutomaticConversionSettings,
        bool]:
        """
        Get the configured permission for automatic conversion from messages (links, snippets, etc.)

        :param _id: The guild ID to get the permission value for
        :param did_exist: If to return whether if the guild document existed, or if the value is default
        :return: The permission value, by default env[AUTOCONV_DEFAULT]
        """
        _did_exist: bool = False

        if cached := self.bot.get_cache_v('autoconv', _id):
            _did_exist: bool = True
            permission: AutomaticConversionSettings = cached
            self.bot.logger.debug('Returning cached auto values for identity "%d"', _id)
        else:
            stored: Optional[GitBotGuild] = await self.find_one({'_id': _id})
            if stored:
                permission: AutomaticConversionSettings = stored.get('autoconv', self.bot.mgr.env.autoconv_default)
                _did_exist: bool = True
            else:
                permission: AutomaticConversionSettings = self.bot.mgr.env.autoconv_default
            self.bot.set_cache_v('autoconv', _id, permission)
        return permission if not did_exist else (permission, _did_exist)
