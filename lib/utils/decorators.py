import re
import functools
import inspect
from discord.ext import commands
from typing import Callable, Any, Optional, Generator
from lib.utils import regex
from lib.typehints import GitHubRepository, CommandHelp, ArgumentExplainer, LocaleName, CommandGroupHelp


class GitBotCommand(commands.Command):
    def __init__(self, func: Callable, **kwargs):
        super().__init__(func, **kwargs)
        self._cached_help_contents: dict[LocaleName, CommandHelp] = {}

    @property
    def fullname(self) -> str:
        return self.name if not self.full_parent_name else f'{self.full_parent_name} {self.name}'

    @property
    def underscored_name(self) -> str:
        return self.fullname.lower().replace(' ', '_')

    def get_argument_explainers(self, ctx: commands.Context) -> Generator[ArgumentExplainer, None, None]:
        for explainer in self.get_help_content(ctx)['argument_explainers']:
            yield ctx.l.help.argument_explainers[explainer]

    def get_qa_disclaimer(self, ctx: commands.Context) -> Optional[str]:
        return ctx.l.help.qa_disclaimers.get(self.get_help_content(ctx)['qa_resource'])

    def get_permissions(self, ctx: commands.Context) -> Generator[str, None, None]:
        for permission_resource_name in self.get_help_content(ctx)['required_permissions']:
            yield ctx.l.permissions[permission_resource_name]

    def get_help_content(self, ctx: commands.Context) -> Optional[CommandHelp]:
        if cached := self._cached_help_contents.get(ctx.l.meta.name):
            return cached
        help_: CommandHelp = ctx.l.help.commands.get(self.underscored_name)
        if not help_:
            return
        help_.setdefault(self.fullname)
        self._cached_help_contents[ctx.l.meta.name] = help_
        return help_

    def __str__(self) -> str:
        return self.fullname


class GitBotCommandGroup(commands.Group, GitBotCommand):
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

    def get_help_content(self, ctx: commands.Context, command_contents: bool = False) -> Optional[CommandGroupHelp]:
        help_: CommandHelp | CommandGroupHelp = super().get_help_content(ctx)
        if not help_:
            return
        help_.setdefault('commands', self.commands if not command_contents else [cmd.get_help_content(ctx)
                                                                                 for cmd in self.commands])
        return help_


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
            def normalize_id(_id: int | str | commands.Context) -> int:
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
            match_: list = re.findall(regex.GITHUB_REPO_GIT_URL_RE, repo) or re.findall(regex.GITHUB_REPO_URL_RE, repo)
            if match_:
                return f'{match_[0][0]}/{match_[0][1]}'
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

    def decorator(func) -> commands.Command:
        return cls(func, name=name, **_inject_aliases(name, **attrs))

    return decorator


def gitbot_group(name: str, **attrs) -> Callable:
    """
    A group decorator that automatically injects "-" and "--" aliases.

    :param name: The group name
    :param attrs: Additional attributes
    """

    def decorator(func) -> GitBotCommandGroup:
        return GitBotCommandGroup(func, name=name, **_inject_aliases(name, **attrs))

    return decorator
