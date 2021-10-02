import re
import functools
import inspect
from discord.ext import commands
from typing import Callable, Union, Any, Optional
from lib.utils import regex
from lib.typehints import GitHubRepository


class _GitBotCommandGroup(commands.Group):
    def __init__(self, func, **attrs):
        super().__init__(func, **attrs)

    def command(self, *args, **kwargs) -> Callable:
        def decorator(func: Callable) -> commands.Command:
            kwargs.setdefault('parent', self)
            result: commands.Command = gitbot_command(*args, **kwargs)(func)
            self.add_command(result)
            return result

        return decorator

    def group(self, *args, **kwargs) -> Callable:
        def decorator(func: Callable) -> commands.Command:
            kwargs.setdefault('parent', self)
            result: commands.Command = gitbot_group(*args, **kwargs)(func)
            self.add_command(result)
            return result

        return decorator


def _inject_aliases(name: str, **attrs) -> dict:
    def gen_aliases(_name: str) -> tuple:
        return _name, f'-{_name}', f'--{_name}', f'—{_name}', f'——{_name}'

    aliases: list[str] = attrs.get('aliases') or []
    to_add: list[str] = list(sum([gen_aliases(alias) for alias in aliases], ()))
    aliases.extend([*to_add, *(gen_aliases(name)[1:])])
    attrs['aliases']: list[str] = list(set(aliases))
    return attrs


def restricted() -> commands.Command:
    """
    Allow only wulf to use commands with this decorator
    """

    def pred(ctx: commands.Context) -> bool:
        return ctx.author.id == 548803750634979340

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
        kwargs[target]: Any = normalizing_func(param)
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
            def normalize_id(_id: Union[int, str, commands.Context]) -> int:
                return int(_id) if not isinstance(_id, commands.Context) else getattr(_id, context_resource).id

            return normalize_argument(func, '_id', normalize_id, *args, **kwargs)

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
        def normalize_repo(repo: GitHubRepository) -> str:
            if not repo:
                return repo
            repo: str = repo.strip()
            match_: list = re.findall(regex.GITHUB_REPO_GIT_URL, repo) or re.findall(regex.REPO_RE, repo)
            if match_:
                return f'{match_[0][0]}/{match_[0][1]}'
            return repo

        return await normalize_argument(func, 'repo', normalize_repo, *args, **kwargs)  # noqa

    return wrapper


def gitbot_command(name: str, cls=commands.Command, **attrs) -> Callable:
    """
    A command decorator that automatically injects "-" and "--" aliases.

    :param name: The command name
    :param cls: The command class
    :param attrs: Additional attributes
    """

    def decorator(func) -> commands.Command:
        return cls(func, name=name, **_inject_aliases(name, **attrs))

    return decorator


def gitbot_group(name: str, **attrs) -> Callable:
    """
    A group decorator that automatically injects "-" and "--" aliases.

    :param name: The group name
    :param attrs: Additional attributes
    """

    def decorator(func) -> _GitBotCommandGroup:
        return _GitBotCommandGroup(func, name=name, **_inject_aliases(name, **attrs))

    return decorator
