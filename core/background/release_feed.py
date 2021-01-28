import asyncio
import os
import discord
import datetime
from bot import logger
from bs4 import BeautifulSoup
from typing import List, Tuple, Optional
from discord.ext import tasks, commands
from motor.motor_asyncio import AsyncIOMotorClient
from core.bot_config import Git


class ReleaseFeed(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot
        self.db_client: AsyncIOMotorClient = AsyncIOMotorClient(os.getenv('DB_CONNECTION'))
        self.db: AsyncIOMotorClient = self.db_client.store.guilds
        self.release_feed_worker.start()

    @tasks.loop(minutes=45)
    async def release_feed_worker(self) -> None:
        async for doc in self.db.find({}):
            changed: bool = False
            update: list = []
            for item in doc['feed']:
                res: Optional[dict] = await Git.get_latest_release(item['repo'])
                if res:
                    if (t := res['release']['tagName']) != item['release']:
                        await self.handle_feed_item(doc, item, res)
                        changed: bool = True
                    update.append((item['repo'], t))
                else:
                    await self.handle_missing_item(doc, item)
                await asyncio.sleep(2)
            if changed:
                await self.update_with_data(doc['_id'], update)

    async def handle_feed_item(self, doc: dict, item: dict, new_release: dict) -> None:
        stage: str = 'prerelease' if new_release['release']['isPrerelease'] else 'release'
        if new_release['release']['isDraft']:
            stage += ' draft'
        embed: discord.Embed = discord.Embed(
            color=new_release['color'],
            title=f'New {item["repo"]} {stage}! `{new_release["release"]["tagName"]}`',
            url=new_release['release']['url']
        )
        if new_release['usesCustomOpenGraphImage']:
            embed.set_image(url=new_release['openGraphImageUrl'])

        if body := new_release['release']['descriptionHTML']:
            body: str = BeautifulSoup(body, features='html.parser').getText()[:387].replace('\n\n', '\n')
            body: str = f"```{body[:body.rindex(' ')]}...```".strip()

        author: dict = new_release["release"]["author"]
        author: str = f'Created by [{author["login"]}]({author["url"]}) on ' \
                      f'{datetime.datetime.strptime(new_release["release"]["createdAt"], "%Y-%m-%dT%H:%M:%SZ").strftime("%e, %b %Y")}\n'

        asset_c: int = new_release["release"]["releaseAssets"]["totalCount"]
        assets: str = f'Has {asset_c} assets attached\n'.replace('0',
                                                                 'no') if asset_c != 1 else 'Has one asset attached'
        info: str = f'{author}{assets}'

        embed.add_field(name=':notepad_spiral: Body:', value=body, inline=False)
        embed.add_field(name=':mag_right: Info:', value=info)

        await self.doc_send(doc, embed)

    async def update_with_data(self, guild_id: int, to_update: List[Tuple[str]]) -> None:
        await self.db.find_one_and_update({'_id': guild_id}, {
            '$set': {'feed': [dict(repo=repo, release=release) for repo, release in to_update]}})

    async def handle_missing_item(self, doc: dict, item: dict) -> None:
        embed: discord.Embed = discord.Embed(
            color=0xda4353,
            title=f'One of your release feed repos was deleted/renamed!',
            description=f'A repository previously saved as `{item["repo"]}` was **deleted or renamed** by the owner. '
                        f'Please re-add it under the new name.'
        )
        if len(doc['feed']) == 1:
            await self.db.find_one_and_delete(doc)
        else:
            await self.db.update_one(doc, {'$pull': {'feed': item}})
        await self.doc_send(doc, embed)

    @release_feed_worker.before_loop
    async def release_feed_worker_before_loop(self) -> None:
        logger.info('Release worker sleeping until the bot is ready...')
        await self.bot.wait_until_ready()

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild) -> None:
        await self.db.find_one_and_delete({'_id': guild.id})

    async def doc_send(self, doc: dict, embed: discord.Embed) -> bool:
        try:
            webhook: discord.Webhook = discord.Webhook.from_url('https://discord.com/api/webhooks/' + doc['hook'],
                                                                adapter=discord.AsyncWebhookAdapter(Git.ses))
            await webhook.send(embed=embed, username=self.bot.user.name, avatar_url=self.bot.user.avatar_url)
        except (discord.errors.NotFound, discord.errors.Forbidden, discord.errors.HTTPException):
            await self.db.find_one_and_delete({'_id': doc['_id']})
            return False
        return True


def setup(bot: commands.Bot) -> None:
    bot.add_cog(ReleaseFeed(bot))
