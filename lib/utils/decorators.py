import re
import functools
import inspect
from discord.ext import commands
from typing import Callable, Union, Any, Coroutine, List
from lib.utils import regex


class _GitBotCommandGroup(commands.Group):
    def __init__(self, func, **attrs):
        super().__init__(func, **attrs)

    def command(self, *args, **kwargs) -> Callable:
        def decorator(func: Coroutine) -> commands.Command:
            kwargs.setdefault('parent', self)
            result: commands.Command = gitbot_command(*args, **kwargs)(func)
            self.add_command(result)
            return result

        return decorator

    def group(self, *args, **kwargs) -> Callable:
        def decorator(func: Coroutine) -> commands.Command:
            kwargs.setdefault('parent', self)
            result: commands.Command = gitbot_group(*args, **kwargs)(func)
            self.add_command(result)
            return result

        return decorator


def _inject_aliases(name: str, **attrs) -> dict:
    def gen_aliases(_name: str) -> tuple:
        return _name, f'-{_name}', f'--{_name}'

    aliases: List[str] = attrs.get('aliases') or []
    to_add: List[str] = list(sum([gen_aliases(alias) for alias in aliases], ()))
    aliases.extend([*to_add, *(gen_aliases(name)[1:])])
    attrs['aliases']: List[str] = list(set(aliases))
    return attrs


def restricted() -> commands.Command:
    """
    Allow only wulf to use commands with this decorator
    """

    def pred(ctx: commands.Context) -> bool:
        return ctx.author.id == 548803750634979340

    return commands.check(pred)


def normalize_argument(func: Union[Callable, Coroutine],
                       target: str,
                       normalizing_func: Callable,
                       /,
                       *args,
                       **kwargs) -> Union[Callable, Coroutine]:
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


def normalize_identity(func: Union[Callable, Coroutine]) -> Union[Callable, Coroutine]:
    """
    Normalize the _id argument to be an instance of :class:`int`
    (instead of potential :class:`str` or :class:`discord.ext.commands.Context`

    :param func: The function to wrap with this decorator
    :return: The function with the _id argument normalized
    """

    def wrapper(*args: tuple, **kwargs: dict) -> Any:
        def normalize_id(_id: Union[int, str, commands.Context]) -> int:
            return int(_id) if not isinstance(_id, commands.Context) else _id.author.id

        return normalize_argument(func, '_id', normalize_id, *args, **kwargs)

    return wrapper


def normalize_repository(func: Union[Callable, Coroutine]) -> Union[Callable, Coroutine]:
    """
    Normalize the repo argument to be in the owner/repo-name format if possible.
    It's important to place this UNDER discord-specific decorators in commands.

    :param func: The function to wrap with this decorator
    :return: The function with the repo argument normalized
    """

    @functools.wraps(func)
    async def wrapper(*args: tuple, **kwargs: dict) -> Any:
        def normalize_repo(repo: str) -> str:
            if not repo:
                return repo
            repo: str = repo.strip()
            match: list = re.findall(regex.GITHUB_REPO_GIT_URL, repo) or re.findall(regex.GITHUB_REPO_URL, repo)
            if match:
                return f'{match[0][0]}/{match[0][1]}'
            return repo

        return await normalize_argument(func, 'repo', normalize_repo, *args, **kwargs)

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
