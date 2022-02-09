"""
A one-use script to change old-style guild documents into ones with new Multi-Release-Feed functionality.
"""

import discord
import requests
from pymongo import MongoClient, UpdateOne
from dotenv import load_dotenv
from os import getenv

load_dotenv()

db: MongoClient = MongoClient(getenv('DB_CONNECTION'))['store']['guilds']
ops: list = []
adapter: discord.RequestsWebhookAdapter = discord.RequestsWebhookAdapter(requests.session())

for g in db.find({'hook': {'$exists': True}}):  # Has a top level 'hook' key
    webhook: discord.Webhook = discord.Webhook.from_url('https://discord.com/api/webhooks/' + g['hook'],
                                                        adapter=adapter)
    new_rfi: dict = {'cid': webhook.channel_id,
                     'hook': g['hook'],
                     'repos': [{'name': old_rfi['repo'],
                                'tag': old_rfi['release']} for old_rfi in g['feed']]}
    ops.append(UpdateOne(g, {'$set': {'feed': [new_rfi]}, '$unset': {'hook': ''}}))


print("Writing " + str(len(ops)))
db.bulk_write(ops, ordered=False)
print("Updated " + str(len(ops)))
