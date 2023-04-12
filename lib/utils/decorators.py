import builtins
import re
import functools
import inspect
import discord
from discord.ext import commands
from typing import Callable, Any, Optional, Union, TYPE_CHECKING
if TYPE_CHECKING:
    from lib.structs.discord.context import GitBotContext
    from lib.typehints import ReleaseFeed
from lib import structs
from lib.utils import regex
from lib.structs.discord.commands import GitBotCommand, GitBotGroup, GitBotHybridCommand, GitBotHybridGroup


def _inject_aliases(name: str, **attrs) -> dict:
    def gen_aliases(_name: str) -> tuple:
        return _name, f'-{_name}', f'--{_name}', f'—{_name}', f'——{_name}'

    aliases: list[str] = attrs.get('aliases') or []
    to_add: list[str] = list(sum([gen_aliases(alias) for alias in aliases], ()))
    aliases.extend([*to_add, *(gen_aliases(name)[1:])])
    attrs['aliases'] = list(set(aliases))
    return attrs


def bot_can_manage_release_feed_channels():
    """
    Check if the bot can manage release feed channels
    """

    async def pred(ctx: 'GitBotContext') -> bool:
        rf: Optional['ReleaseFeed'] = (await ctx.bot.mgr.db.guilds.find_one({'_id': ctx.guild.id}) or {}).get('feed', None)
        if rf:
            for rfi in rf:
                channel: discord.TextChannel = await ctx.bot.fetch_channel(rfi['cid'])
                if not channel.permissions_for(ctx.guild.me).manage_channels:
                    ctx.check_failure_code = structs.CheckFailureCode.MISSING_RELEASE_FEED_CHANNEL_PERMISSIONS_GUILDWIDE
                    return False
        return True

    return commands.check(pred)


def guild_has_release_feeds():
    """
    Check if the guild has any release feeds
    """

    async def pred(ctx: 'GitBotContext') -> bool:
        rf: Optional['ReleaseFeed'] = (await ctx.bot.mgr.db.guilds.find_one({'_id': ctx.guild.id}) or {}).get('feed', None)
        if not rf:
            ctx.check_failure_code = structs.CheckFailureCode.NO_GUILD_RELEASE_FEEDS
            return False
        return True

    return commands.check(pred)


def restricted():
    """
    Allow only wulf to use commands with this decorator
    """

    def pred(ctx: 'GitBotContext') -> bool:
        return ctx.author.id == ctx.bot.mgr.env.owner_id

    return commands.check(pred)


def validate_github_name(param_name: Optional[str] = None, default: Any = None):
    """
    Validate a specific function argument against a regex that matches valid GitHub user-or-org names

    :param param_name: The parameter name of the argument to validate
    :param default: The default value to return if
                    the match doesn't succeed (the default return of the decorated function)
    :return: The function with the argument validated or the default return
    """

    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            arg: str = (kwargs[param_name] if param_name in kwargs
                        else args[list(inspect.getfullargspec(func).args).index(param_name)])
            if regex.GITHUB_NAME_RE.match(arg):
                return await func(*args, **kwargs)
            return default

        return wrapper

    return decorator


def normalize_argument(func: Callable,
                       target: str,
                       normalizing_func: Callable[[Any], Any],
                       /,
                       *args,
                       **kwargs) -> Callable:
    """
    Normalize an argument in a function call.
    Mainly meant to be used inside decorators.
    The function is not called inside this helper, a partial is returned.

    :param func: The function which arguments should be normalized
    :param target: The argument to be normalized
    :param normalizing_func: The function to apply to the argument in order to normalize it
    :param args: The arguments in the function call
    :param kwargs: The keyword arguments in the function call
    :return: The function with the arguments normalized
    """
    if target in kwargs:
        param: Any = kwargs[target]
        kwargs[target] = normalizing_func(param)
    else:
        spec: inspect.FullArgSpec = inspect.getfullargspec(func)
        if target in spec.args:
            args: list = list(args)
            index: int = spec.args.index(target)
            args[index] = normalizing_func(args[index])
    return func(*args, **kwargs)


def normalize_identity(context_resource: str = 'author') -> Callable:
    """
    Normalize the _id argument to be an instance of :class:`int`
    (instead of potential :class:`str` or :class:`discord.ext.commands.Context`

    :param context_resource: The middle attribute to get the ID attribute of in case of Context as _id
    :return: The function with the _id argument normalized
    """

    def decorator(func: Callable) -> Callable:
        def wrapper(*args: tuple, **kwargs: dict) -> Any:
            def normalize_id(_id: Union[int | str, 'GitBotContext']) -> int:
                return int(_id) if not isinstance(_id, commands.Context) else getattr(_id, context_resource).id

            return normalize_argument(func, '_id', normalize_id, *args, **kwargs)

        return wrapper

    return decorator


def uses_quick_access(resource: str, parameter_name: str):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            ctx: 'GitBotContext' = args[1]
            spec: inspect.FullArgSpec = inspect.getfullargspec(func)
            args: list = list(args)
            index: int = spec.args.index(parameter_name)
            passed: str | None = args[index] if index < len(args) else kwargs.get(parameter_name, None)
            if parameter_name in spec.args and passed is None:
                stored: str = await ctx.bot.mgr.db.users.getitem(ctx, 'repo')
                if not stored:
                    await ctx.bot.mgr.db.users.delitem(ctx, 'repo')
                    await ctx.error(ctx.l.generic.nonexistent.repo.qa)
                    return
                elif not await ctx.bot.github.rest_get_repo(stored):  # check if repo is valid; rate-limit intensive
                    await ctx.bot.mgr.db.users.delitem(ctx, 'repo')
                    await ctx.error(ctx.l.generic.nonexistent.repo.qa_changed)
                    return
                if parameter_name in kwargs:
                   kwargs[parameter_name] = stored
                else:
                    args[index] = stored
            return await func(*args, **kwargs)

        return wrapper

    return decorator


def normalize_repository(func: Callable) -> Callable:
    """
    Normalize the repo argument to be in the owner/repo-name format if possible.
    It's important to place this UNDER discord-specific decorators in commands.

    :param func: The function to wrap with this decorator
    :return: The function with the repo argument normalized
    """

    @functools.wraps(func)
    async def wrapper(*args: tuple, **kwargs: dict) -> Any:
        def normalize_repo(repo: Any) -> str:
            match type(repo):
                case builtins.str:
                    repo: str = repo.strip()
                    match_: list = re.findall(regex.GITHUB_REPO_GIT_URL_RE, repo) or re.findall(regex.GITHUB_REPO_URL_RE, repo)
                    return match_[0] if match_ else repo
                case structs.ParsedRepositoryData | builtins.tuple:
                    return getattr(repo, 'slashname', f'{repo[0]}/{repo[1]}')
                case builtins.dict:
                    return repo.get('full_name')
                case _:
                    return repo

        return await normalize_argument(func, 'repo', normalize_repo, *args, **kwargs)  # noqa

    return wrapper


def gitbot_command(name: str, cls=GitBotCommand, **attrs) -> Callable:
    """
    A command decorator that automatically injects "-" and "--" aliases.

    :param name: The command name
    :param cls: The command class
    :param attrs: Additional attributes
    """

    def decorator(func) -> GitBotCommand:
        return cls(func, name=name, **_inject_aliases(name, **attrs))

    return decorator


def gitbot_group(name: str, cls=GitBotGroup, **attrs) -> Callable:
    """
    A group decorator that automatically injects "-" and "--" aliases.

    :param name: The group name
    :param cls: The command group class
    :param attrs: Additional attributes
    """

    def decorator(func) -> GitBotGroup:
        return cls(func, name=name, **_inject_aliases(name, **attrs))

    return decorator


def gitbot_hybrid_command(name: str, cls=GitBotHybridCommand, **attrs) -> Callable:
    """
    A hybrid group decorator that automatically injects "-" and "--" aliases.

    :param name: The group name
    :param cls: The command group class
    :param attrs: Additional attributes
    """

    def decorator(func) -> GitBotHybridCommand:
        return cls(func, name=name, **_inject_aliases(name, **attrs))

    return decorator


def gitbot_hybrid_group(name: str, cls=GitBotHybridGroup, **attrs) -> Callable:
    """
    A hybrid group decorator that automatically injects "-" and "--" aliases.

    :param name: The group name
    :param cls: The command group class
    :param attrs: Additional attributes
    """

    def decorator(func) -> GitBotHybridGroup:
        return cls(func, name=name, **_inject_aliases(name, **attrs))

    return decorator
