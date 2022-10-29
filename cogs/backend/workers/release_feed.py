import discord
import datetime
from os import environ
from bs4 import BeautifulSoup
from typing import Optional
from discord.ext import tasks, commands
from lib.structs.discord.bot import GitBot
from lib.typehints import ReleaseFeedItem, ReleaseFeedRepo, GitBotGuild, TagNameUpdateData


class ReleaseFeedWorker(commands.Cog):
    def __init__(self, bot: GitBot):
        self.bot: GitBot = bot
        self.iterno: int = 0
        if self.bot.mgr.env.run_release_feed_worker:
            self.release_feed_worker.start()
        else:
            self.bot.mgr.log("Release feed worker is disabled - env.run_release_feed_worker == False")

    @property
    def pretty_iterno(self):
        return f'#{str(self.iterno).zfill(3)}'

    async def update_tag_names_with_data(self,
                                         guild: GitBotGuild,
                                         update_data: list[TagNameUpdateData]) -> None:
        feed = guild['feed']
        for ud in update_data:
            (_repos := feed[feed.index(ud.rfi)]['repos'])[_repos.index(ud.rfr)] = {'name': ud.rfr['name'],
                                                                                   'tag': ud.tag}
        await self.bot.mgr.db.guilds.find_one_and_update({'_id': guild['_id']}, {'$set': {'feed': feed}})

    @tasks.loop(minutes=int(environ.get('release_feed_worker_interval', '15')))
    async def release_feed_worker(self) -> None:
        self.iterno += 1
        self.bot.mgr.debug(f'Starting worker cycle {self.pretty_iterno}')
        async for guild in self.bot.mgr.db.guilds.find({'feed': {'$exists': True}}):
            self.bot.mgr.debug(f'Handling GID {guild["_id"]}')
            guild: GitBotGuild
            changed: bool = False
            update: list = []
            for rfi in guild['feed']:
                for repo in rfi['repos']:
                    res: Optional[dict] = await self.bot.github.get_latest_release(repo['name'])
                    if res:
                        if res['release'] and (t := res['release']['tagName']) != repo['tag']:
                            await self.handle_feed_repo(guild, repo, rfi, res)
                            changed: bool = True
                            update.append(TagNameUpdateData(rfi, repo, t))
                            self.bot.mgr.debug(f'New release found for repo "{repo["name"]}" (tag: {repo["tag"]})'
                                               f' in GID {guild["_id"]}')
                        else:
                            self.bot.mgr.debug(f'No new release for repo "{repo["name"]}" (tag: {repo["tag"]})'
                                               f' in GID {guild["_id"]}')
                    else:
                        self.bot.mgr.debug(f'Missing repo detected in GID {guild["_id"]} ("{repo["name"]}")')
                        await self.handle_missing_feed_repo(guild, rfi, repo)
            if changed:
                self.bot.mgr.debug(f'Changes detected in GID {guild["_id"]}')
                await self.update_tag_names_with_data(guild, update)
            else:
                self.bot.mgr.debug(f'Finished worker cycle for GID {guild["_id"]} - nothing changed')

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
            body: str = ' '.join(BeautifulSoup(body, features='html.parser').getText().split())
            body: str = f"```{self.bot.mgr.truncate(body, 400, full_word=True)}```".strip()

        author: dict = new_release["release"]["author"]
        author: str = f'Created by [{author["login"]}]({author["url"]}) on ' \
                      f'{datetime.datetime.strptime(new_release["release"]["createdAt"], "%Y-%m-%dT%H:%M:%SZ").strftime("%e, %b %Y")}\n'

        asset_c: int = new_release["release"]["releaseAssets"]["totalCount"]
        assets: str = f'Has {asset_c} assets attached\n'.replace('0', 'no') if asset_c != 1 else 'Has one asset attached'
        info: str = f'{author}{assets}'
        embed.add_field(name=':notepad_spiral: Body:', value=body, inline=False)
        embed.add_field(name=':mag_right: Info:', value=info)
        await self.send_to_rfi(guild, rfi, embed,
                               self.bot.mgr.release_feed_mention_to_actual(rfi['mention']) if rfi.get('mention') else None)

    async def handle_missing_feed_repo(self, guild: GitBotGuild, rfi: ReleaseFeedItem, repo: ReleaseFeedRepo) -> None:
        embed: discord.Embed = discord.Embed(
            color=0xda4353,
            title=f'One of your release feed repos was deleted/renamed!',
            description=f'A repository previously saved as `{repo["name"]}` was **deleted or renamed** by the owner. '
                        f'Please re-add it under the new name.'
        )
        await self.bot.mgr.db.guilds.update_one(guild, {'$pull': {f'feed.{guild["feed"].index(rfi)}.repos': repo}})
        await self.send_to_rfi(guild, rfi, embed)

    @release_feed_worker.before_loop
    async def release_feed_worker_before_loop(self) -> None:
        self.bot.logger.info('Release worker sleeping until the bot is ready...')
        await self.bot.wait_until_ready()

    async def send_to_rfi(self,
                          guild: GitBotGuild,
                          rfi: ReleaseFeedItem,
                          embed: Optional[discord.Embed] = None,
                          text: Optional[str] = None) -> bool:
        try:
            webhook: discord.Webhook = discord.Webhook.from_url('https://discord.com/api/webhooks/' + rfi['hook'],
                                                                session=self.bot.session)
            await webhook.send(text, embed=embed, username=self.bot.user.name, avatar_url=self.bot.user.avatar.url)
        except (discord.errors.NotFound, discord.errors.Forbidden, discord.errors.HTTPException):
            await self.bot.mgr.db.guilds.find_one_and_delete({'_id': guild['_id']})
            return False
        return True


async def setup(bot: GitBot) -> None:
    await bot.add_cog(ReleaseFeedWorker(bot))
