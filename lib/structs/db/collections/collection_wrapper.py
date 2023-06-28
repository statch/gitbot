# coding: utf-8
from motor.motor_asyncio import AsyncIOMotorCollection
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lib.structs.discord.bot import GitBot
    from lib.structs.db.database_proxy import DatabaseProxy


class CollectionWrapper(AsyncIOMotorCollection):
    __wrapped_collection_name__: str

    """
    A wrapper around :class:`AsyncIOMotorCollection` allowing for easy extension of MongoDB collections.
    """

    def __init__(self, db: 'DatabaseProxy', collection_name: str, *args, **kwargs):
        self.db: 'DatabaseProxy' = db
        self.bot: 'GitBot' = db.bot
        super().__init__(db.actual_db, collection_name, *args, **kwargs)
