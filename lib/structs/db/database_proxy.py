# coding: utf-8

import certifi
from motor import motor_asyncio as ma
from typing import TYPE_CHECKING
from lib.structs import DictProxy
from .collections import UsersCollection, GuildsCollection

if TYPE_CHECKING:
    import aiohttp
    from lib.structs.discord.bot import GitBot


class DatabaseProxy:
    """
    An abstraction layer for the database, allowing for easy access to the database and its collections,
    allowing for safe and efficient manipulation and retrieval of data.
    """

    def __init__(self, bot: 'GitBot'):
        self.bot: 'GitBot' = bot
        self.ses: 'aiohttp.ClientSession' = self.bot.session
        self._env: DictProxy = self.bot.mgr.env
        self._ca_cert: str = certifi.where()
        self.client: ma.AsyncIOMotorClient = ma.AsyncIOMotorClient(self._env.db_connection,
                                                                   appname=self.bot.mgr.bot_dev_name,
                                                                   tls=self._env.db_use_tls,
                                                                   tlsCAFile=self._ca_cert,
                                                                   tlsAllowInvalidCertificates=False)
        self._actual_db: ma.AsyncIOMotorDatabase = self.client.get_database('store' if self._env.production else 'test')
        self.users: ma.AsyncIOMotorCollection = UsersCollection(self)
        self.guilds: ma.AsyncIOMotorCollection = GuildsCollection(self)


    @property
    def actual_db(self) -> ma.AsyncIOMotorDatabase:
        """
        The database to be used in the current environment, "store" if production, "test" if not.
        """
        return self._actual_db
