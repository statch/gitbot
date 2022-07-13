import discord
import datetime
from motor.motor_asyncio import AsyncIOMotorCursor
from bot import logger
from bs4 import BeautifulSoup
from typing import Optional
from discord.ext import tasks, commands
from lib.globs import Git, Mgr
from lib.typehints import ReleaseFeedItem, ReleaseFeedRepo, GitBotGuild, TagNameUpdateData


class ReleaseFeedWorker(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot
        if Mgr.env.run_release_feed_worker:
            self.release_feed_worker.start()
        else:
            Mgr.log("Release feed worker is disabled - env.run_release_feed_worker == False")

    @tasks.loop(minutes=45)
    async def release_feed_worker(self) -> None:
        Mgr.debug('Starting worker cycle')
        query: AsyncIOMotorCursor = Mgr.db.guilds.find({'feed': {'$exists': True}})
        async for guild in query:
            Mgr.debug(f'Handling GID {guild["_id"]}')
            guild: GitBotGuild
            changed: bool = False
            update: list = []
            for rfi in guild['feed']:
                for repo in rfi['repos']:
                    res: Optional[dict] = await Git.get_latest_release(repo['name'])
                    if res:
                        if res['release'] and (t := res['release']['tagName']) != repo['tag']:
                            await self.handle_feed_repo(guild, repo, rfi, res)
                            changed: bool = True
                            update.append(TagNameUpdateData(rfi, repo, t))
                            Mgr.debug(f'New release found for repo "{repo["name"]}" (tag: {repo["tag"]})'
                                      f' in GID {guild["_id"]}')
                        else:
                            Mgr.debug(f'No new release for repo "{repo["name"]}" (tag: {repo["tag"]})'
                                      f' in GID {guild["_id"]}')
                    else:
                        Mgr.debug(f'Missing repo detected in GID {guild["_id"]} ("{repo["name"]}")')
                        await self.handle_missing_feed_repo(guild, rfi, repo)
            if changed:
                Mgr.debug(f'Changes detected in GID {guild["_id"]}')
                await self.update_tag_names_with_data(guild, update)
            else:
                Mgr.debug(f'Finished worker cycle for GID {guild["_id"]} - nothing changed')

    async def handle_feed_repo(self,
                               guild: GitBotGuild,
                               repo: ReleaseFeedRepo,
                               rfi: ReleaseFeedItem,
                               new_release: dict) -> None:
        stage: str = 'prerelease' if new_release['release']['isPrerelease'] else 'release'
        if new_release['release']['isDraft']:
            stage += ' draft'
        embed: discord.Embed = discord.Embed(
            color=new_release['color'],
            title=f'New {repo["name"]} {stage}! `{new_release["release"]["tagName"]}`',
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
        assets: str = f'Has {asset_c} assets attached\n'.replace('0', 'no') if asset_c != 1 else 'Has one asset attached'
        info: str = f'{author}{assets}'
        embed.add_field(name=':notepad_spiral: Body:', value=body, inline=False)
        embed.add_field(name=':mag_right: Info:', value=info)
        await self.send_to_rfi(guild, rfi, embed,
                               Mgr.release_feed_mention_to_actual(rfi['mention']) if rfi['mention'] else None)

    async def update_tag_names_with_data(self,
                                         guild: GitBotGuild,
                                         update_data: list[TagNameUpdateData]) -> None:
        feed = guild['feed']
        for ud in update_data:
            (_repos := feed[feed.index(ud.rfi)]['repos'])[_repos.index(ud.rfr)] = {'name': ud.rfr['name'],
                                                                                   'tag': ud.tag}
        await Mgr.db.guilds.find_one_and_update({'_id': guild['_id']}, {'$set': {'feed': feed}})

    async def handle_missing_feed_repo(self, guild: GitBotGuild, rfi: ReleaseFeedItem, repo: ReleaseFeedRepo) -> None:
        embed: discord.Embed = discord.Embed(
            color=0xda4353,
            title=f'One of your release feed repos was deleted/renamed!',
            description=f'A repository previously saved as `{repo["name"]}` was **deleted or renamed** by the owner. '
                        f'Please re-add it under the new name.'
        )
        await Mgr.db.guilds.update_one(guild, {'$pull': {f'feed.{guild["feed"].index(rfi)}.repos': repo}})
        await self.send_to_rfi(guild, rfi, embed)

    @release_feed_worker.before_loop
    async def release_feed_worker_before_loop(self) -> None:
        logger.info('Release worker sleeping until the bot is ready...')
        await self.bot.wait_until_ready()

    async def send_to_rfi(self,
                          guild: GitBotGuild,
                          rfi: ReleaseFeedItem,
                          embed: Optional[discord.Embed] = None,
                          text: Optional[str] = None) -> bool:
        try:
            webhook: discord.Webhook = discord.Webhook.from_url('https://discord.com/api/webhooks/' + rfi['hook'],
                                                                adapter=discord.AsyncWebhookAdapter(Git.ses))
            await webhook.send(text, embed=embed, username=self.bot.user.name, avatar_url=self.bot.user.avatar_url)
        except (discord.errors.NotFound, discord.errors.Forbidden, discord.errors.HTTPException):
            await Mgr.db.guilds.find_one_and_delete({'_id': guild['_id']})
            return False
        return True


def setup(bot: commands.Bot) -> None:
    bot.add_cog(ReleaseFeedWorker(bot))
