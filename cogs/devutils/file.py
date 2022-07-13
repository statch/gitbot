import discord
import hashlib
from typing import Optional
from discord.ext import commands
from lib.globs import Mgr
from lib.utils.decorators import gitbot_group
from lib.structs.discord.context import GitBotContext
from lib.structs.discord.embed import GitBotEmbed


class FileDevutils(commands.Cog):
    __valid_hash_algos__: tuple = ('md5', 'sha1', 'sha256', 'sha512', 'sha224', 'sha384')

    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot

    @staticmethod
    async def get_filehash(attachment: discord.Attachment, hash_type: str) -> str:
        hash_ = hashlib.new(hash_type)
        async for chunk in (await Mgr.ses.get(attachment.url)).content.iter_chunked(4096):
            hash_.update(chunk)
        return hash_.hexdigest()

    @staticmethod
    async def send_invalid_algorithm_embed(ctx: GitBotContext):
        invalid_algo_embed: GitBotEmbed = GitBotEmbed(
                title=ctx.l.file.generic_algo_related.invalid_algorithm_embed.title,
                description=ctx.l.file.generic_algo_related.invalid_algorithm_embed.description.format(
                        ' '.join([f'`{a}`' for a in FileDevutils.__valid_hash_algos__])),
                color=Mgr.c.discord.yellow,
                footer=ctx.l.file.generic_algo_related.invalid_algorithm_embed.footer
        )
        return await invalid_algo_embed.send(ctx)

    @staticmethod
    async def hashutil_command_pred(ctx: GitBotContext,
                                    algorithm: str | None) -> (bool, discord.Attachment | None, str | None):
        if not algorithm:
            algorithm: str = 'sha256'
            await ctx.info(ctx.lp.using_sha256_default)
        algorithm: str = algorithm.lower()
        if not ctx.message.attachments:
            await ctx.error(ctx.lp.no_file)
            return False, None, None
        if algorithm not in FileDevutils.__valid_hash_algos__:
            await FileDevutils.send_invalid_algorithm_embed(ctx)
            return False, None, None
        return True, ctx.message.attachments[0], algorithm

    @gitbot_group('file', invoke_without_command=True)
    @commands.cooldown(5, 30, commands.BucketType.user)
    async def file_command_group(self, ctx: GitBotContext) -> None:
        return await ctx.group_help()

    @file_command_group.command(name='hash', aliases=['checksum'])
    @commands.cooldown(5, 30, commands.BucketType.user)
    async def file_hash_command(self, ctx: GitBotContext,
                                algorithm: Optional[str] = None):
        ctx.fmt.set_prefix('file hash')
        c, attachment, algorithm = await FileDevutils.hashutil_command_pred(ctx, algorithm)
        if c:
            checksum: str = await self.get_filehash(attachment, algorithm)
            result_embed: GitBotEmbed = GitBotEmbed(
                    title=':mag:  ' + ctx.fmt('result_embed_title', f'`{algorithm}`', f'`{attachment.filename}`'),
                    description=f'```{checksum}```',
                    color=Mgr.c.discord.green,
                    url=attachment.url
            )
            await result_embed.send(ctx)

    @file_command_group.command(name='verify')
    @commands.cooldown(5, 30, commands.BucketType.user)
    async def file_verify_checksum_command(self, ctx: GitBotContext, checksum: str, algorithm: Optional[str] = None):
        ctx.fmt.set_prefix('file verify')
        c, attachment, algorithm = await FileDevutils.hashutil_command_pred(ctx, algorithm)
        if c:
            to_compare: str = await self.get_filehash(attachment, algorithm)
            if to_compare == checksum:
                result_embed: GitBotEmbed = GitBotEmbed.from_locale_resource(ctx,
                                                                             'file verify result_embed success',
                                                                             color=Mgr.c.discord.green)
            else:
                result_embed: GitBotEmbed = GitBotEmbed.from_locale_resource(ctx,
                                                                             'file verify result_embed failure',
                                                                             color=Mgr.c.discord.red)
                result_embed.description += f'\n```diff\n+ {checksum}\n- {to_compare}```'
            await result_embed.send(ctx)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(FileDevutils(bot))
