"""
A one-use script to replace documents using both the _id and user_id fields
with ones overwriting the _id field.
"""

from pymongo import MongoClient, InsertOne, DeleteOne
from dotenv import load_dotenv
from os import getenv

load_dotenv()

db: MongoClient = MongoClient(getenv('DB_CONNECTION'))['store']['users']

ops: list = []

for u in db.find():
    if 'user_id' in u:
        uid: int = u['user_id']
        del u['_id'], u['user_id']
        ops.append(DeleteOne({'user_id': uid}))
        ops.append(InsertOne(dict(_id=uid, **u)))

print("Writing " + str(len(ops)))
db.bulk_write(ops, ordered=False)
print("Updated " + str(len(ops) >> 1))
