# coding: utf-8

"""
An organized way to manage the different locales,
the database, and other utilities used by GitBot.
It ties these modules together creating a single, performant interface.
~~~~~~~~~~~~~~~~~~~
GitBot utility class providing an elegant way to manage different aspects of the bot
:copyright: (c) 2020-present statch
:license: CC BY-NC-ND 4.0, see LICENSE for more details.
"""

import re
import os
import ast
import json
import string
import dotenv
import base64
import asyncio
import discord
import zipfile
import os.path
import inspect
import hashlib
import certifi
import operator
import datetime
import functools
import subprocess
import dotenv.parser
from copy import deepcopy
from sys import getsizeof
from itertools import chain
from fuzzywuzzy import fuzz
from collections import deque
from lib.utils import regex as r
from discord.ext import commands
from urllib.parse import quote_plus
from collections.abc import Collection
from pipe import traverse, where, select
from lib.utils.decorators import normalize_identity
from lib.structs import (DirProxy, DictProxy,
                         GitCommandData, UserCollection,
                         TypedCache, SelfHashingCache,
                         CacheSchema, ParsedRepositoryData)
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection  # noqa
from typing import Optional, Callable, Any, Reversible, Iterable, Type, TYPE_CHECKING, Generator
if TYPE_CHECKING:
    from lib.structs.discord.context import GitBotContext
    from lib.api.github import GitHubAPI
    from lib.structs.discord.bot import GitBot
from lib.typehints import DictSequence, AnyDict, Identity, GitBotGuild, AutomaticConversionSettings, LocaleName, ReleaseFeedItemMention, GitbotRepoConfig


class Manager:
    """
    A class containing database, locale and utility functions

    :param github: The GitHubAPI instance to use
    :type github: :class:`lib.net.github.api.GitHubAPI`
    """

    def __init__(self, bot: 'GitBot', github: 'GitHubAPI'):
        self.lib_root: str = os.path.dirname(os.path.abspath(__file__))
        self.root_directory: str = self.lib_root[:self.lib_root.rindex(os.sep)]
        self.bot: 'GitBot' = bot
        self.git: 'GitHubAPI' = github
        self._prepare_env()
        self.bot_dev_name: str = f'gitbot ({"production" if self.env.production else "preview"})'
        self._setup_db()
        self.l: DirProxy = self.readdir('resources/locale/', '.locale.json', exclude=('index.json',))
        self.e: DictProxy = self.load_json('emoji')
        self.c: DictProxy = self.load_json('colors', lambda k, v: v if not (isinstance(v, str)
                                                                            and v.startswith('#')) else int(v[1:], 16))
        self.i: DictProxy = self.load_json('images')
        self.locale: DictProxy = self.load_json('locale/index')
        self.licenses: DictProxy = self.load_json('licenses')
        self.carbon_attachment_cache: SelfHashingCache = SelfHashingCache(max_age=60 * 60)
        self.autoconv_cache: TypedCache = TypedCache(CacheSchema(key=int, value=dict))
        self.locale_cache: TypedCache = TypedCache(CacheSchema(key=int, value=str), maxsize=256)
        self.loc_cache: TypedCache = TypedCache(CacheSchema(key=str, value=(dict, tuple)), maxsize=64, max_age=60 * 7)
        self.locale.master = getattr(self.l, str(self.locale.master))
        self.db.users = UserCollection(self.db.users, self.git, self)
        self._missing_locale_keys: dict = {l_['name']: [] for l_ in self.locale['languages']}
        self.localization_percentages: dict[str, float | None] = {l_['name']: None for l_ in self.locale['languages']}
        self.__fix_missing_locales()
        self.__preprocess_locale_emojis()
        # self.__preprocess_localization_percentages()  // TODO: re-enable this once resolved

    async def get_repo_gitbot_config(self, repo: str, fallback_to_dot_json: bool = True) -> GitbotRepoConfig | None:
        gh_res: dict | None = await self.git.get_tree_file(repo, '.gitbot') or \
                              (await self.git.get_tree_file(repo, '.gitbot.json') if fallback_to_dot_json else None)
        if not gh_res:
            return
        if gh_res['encoding'] == 'base64':
            return json.loads(base64.decodebytes(bytes(gh_res['content'].encode('utf-8'))).decode('utf-8'))

    def get_current_commit(self, short: bool = True) -> str:
        """
        Get the current commit hash of the running bot instance.
        Heroku uses the `HEROKU_SLUG_COMMIT` environment variable to store the commit hash,
        but when running locally, the commit hash is stored in the `.git/HEAD` file.

        :return: The current commit hash
        """
        commit: str | None = self.opt(self.env.get(self.env.commit_env_var_name) or self.git_rev_parse_head(),
                                      operator.getitem, slice(7 if short else None))
        return commit if commit else 'unavailable'

    @staticmethod
    def git_rev_parse_head() -> str | None:
        try:
            return subprocess.check_output(['git',
                                            'rev-parse',
                                            'HEAD']).decode('utf-8').strip()
        except subprocess.CalledProcessError:
            return None

    @staticmethod
    def render_label_like_list(labels: Collection[str] | list[dict],
                               *,
                               name_and_url_knames_if_dict: tuple[str, str] | None = None,
                               name_and_url_slug_knames_if_dict: tuple[str, str] | None = None,
                               url_fmt: str = '',
                               max_n: int = 10,
                               total_n: int | None = None) -> str:
        """
        Render a basic codeblock+hyperlink, space-separated list of label-like strings/dicts.

        :param total_n: An integer value representing the length of the `labels` collection to use instead of a len() call
        :param labels: The labels to render, either an iterable[str] or an iterable of dicts representing labels
        :param name_and_url_knames_if_dict: The keys to get for the name and url of the label, if the labels are dicts
        :param name_and_url_slug_knames_if_dict: The keys to get for the name and url slug of the label,
            if the labels are dicts. If this is set, `name_and_url_knames_if_dict` must NOT be set, and `url_fmt` must be set.
        :param url_fmt: The format string to use for the URL of each label
        :param max_n: Max number of labels to render until appending "+(len(labels)-max_n)"
        :return: The rendered labels
        """
        if total_n is None:
            total_n: int = len(labels)

        if name_and_url_knames_if_dict and name_and_url_slug_knames_if_dict:
            raise ValueError('Cannot specify both name_and_url_knames_if_dict and name_and_url_slug_knames_if_dict')
        url_kn_is_slug: bool = False
        if name_and_url_knames_if_dict is not None:
            name_kn, url_kn = name_and_url_knames_if_dict
        elif name_and_url_slug_knames_if_dict is not None:
            url_kn_is_slug: bool = True
            name_kn, url_kn = name_and_url_slug_knames_if_dict
        if url_kn_is_slug and not url_fmt:
            raise ValueError('url_fmt must be specified if urls should be dynamically generated')
        if labels:
            more: str = f' `+{total_n - max_n}`' if total_n > max_n else ''
            is_collection_of_dicts: bool = bool(labels) and isinstance(labels[0], dict)
            if not is_collection_of_dicts:
                l_strings: str = ' '.join([f'[`{l_}`]({url_fmt.format(l_)})' for l_ in labels[:max_n]])
            else:
                l_strings: str = ' '.join(
                    [f'[`{Manager.get_nested_key(l_, name_kn)}`]'  # noqa: no pre-assignment ref
                     f'({url_fmt.format(Manager.get_nested_key(l_, url_kn)) if url_kn_is_slug else Manager.get_nested_key(l_, url_kn)})'  # noqa: ^
                     for l_ in labels[:max_n]])
            return l_strings + more
        return ''

    @staticmethod
    def parse_literal(literal: str) -> str | bytes | int | set | dict | tuple | list | bool | float | None:
        """
        Parse a literal into a Python object

        :param literal: The literal to parse
        :raises ValueError, SyntaxError: If the value is malformed, then ValueError or SyntaxError is raised
        :return: The parsed literal (an object)
        """
        return ast.literal_eval(literal)

    @staticmethod
    def get_closest_match_from_iterable(to_match: str, iterable: Iterable[str]) -> str:
        """
        Iterate through an iterable of :class:`str` and return the item that resembles to_match the most.

        :param to_match: The :class:`str` to pair with a match
        :param iterable: The iterable to search for matches
        :return: The closest match
        """
        best = 0, ''
        for i in iterable:
            if (m := fuzz.token_set_ratio(i := str(i), to_match)) > best[0]:
                best = m, i
        return best[1]

    @staticmethod
    def to_snake_case(string: str) -> str:
        """
        Convert a PascalCase string to snake_case

        :param string: The string to convert
        :return: The converted string
        """
        return ''.join(
            [f'_{i.lower()}' if i.isupper() else i for i in string]
        ).lstrip('_')

    @staticmethod
    def to_github_hyperlink(name: str, codeblock: bool = False) -> str:
        """
        Return f"[{name}](GITHUB_URL)"

        :param name: The GitHub name to embed in the hyperlink
        :param codeblock: Whether to wrap the hyperlink with backticks
        :return: The created hyperlink
        """
        return (f'[{name}](https://github.com/{name.lower()})' if not codeblock
                else f'[`{name}`](https://github.com/{name.lower()})')

    @staticmethod
    def truncate(string: str, length: int, ending: str = '...', full_word: bool = False) -> str:
        """
        Append the ending to the cut string if len(string) exceeds length else return unchanged string.

        .. note ::
            The actual length of the **content** of the string equals length - len(ending) without full_word

        :param string: The string to truncate
        :param length: The desired length of the string
        :param ending: The ending to append
        :param full_word: Whether to cut in the middle of the last word ("pyth...")
                          or to skip it entirely and append the ending
        :return: The truncated (or unchanged) string
        """
        if len(string) > length:
            if full_word:
                string: str = string[:length - len(ending)]
                return f"{string[:string.rindex(' ')]}{ending}".strip()
            return string[:length - len(ending)] + ending
        return string

    @staticmethod
    def flatten(iterable: Iterable) -> Iterable:
        return list(iterable | traverse)

    @staticmethod
    def external_to_discord_timestamp(timestamp: str, ts_format: str) -> str:
        """
        Convert an external timestamp to the <t:timestamp> Discord format

        :param timestamp: The timestamp
        :param ts_format: The format of the timestamp
        :return: The converted timestamp
        """
        return f'<t:{int(datetime.datetime.strptime(timestamp, ts_format).timestamp())}>'

    @staticmethod
    def gen_separator_line(length: Any, char: str = '⎯') -> str:
        """
        Generate a separator line with the provided length or the __len__ of the object passed

        :param length: The length of the separator line
        :param char: The character to use for the separator line
        :return: The separator line
        """
        return char * (length if isinstance(length, int) else len(length))

    @functools.lru_cache()
    def terminal_supports_color(self) -> bool:
        """
        Check if the current terminal supports color.
        """
        return (self.env.terminal_supports_color if not isinstance(self.env.terminal_supports_color, str) else
                self._eval_bool_literal_safe(self.env.terminal_supports_color))

    @staticmethod
    def opt(obj: Any, op: Callable | str | int, /, *args, **kwargs) -> Any:
        """
        Run an operation on an object if bool(object) == True

        :param obj: The object to run the operation on
        :param op: The operation to run if object is True
        :param args: Optional arguments for op
        :param kwargs: Optional keyword arguments for op
        :return: The result of the operation or the unchanged object
        """
        if isinstance(op, (int, str)):
            return obj[op] if obj else obj

        return op(obj, *args, **kwargs) if obj else obj

    @staticmethod
    def getopt(obj: Any, attr: tuple[str, ...] | str | list[str]) -> Any:
        """
        Optional chaining for getting attributes

        :param obj: The object to get the attribute from
        :param attr: The attribute to get
        :return: The attribute or None if it doesn't exist
        """
        if isinstance(attr, str):
            attr: list[str] = attr.split('.')

        for sub_attr in attr:
            obj = getattr(obj, sub_attr, None)
            if obj is None:
                return
        return obj

    @staticmethod
    async def verify_send_perms(channel: discord.TextChannel) -> bool:
        """
        Check if the client can comfortably send a message to a channel

        :param channel: The channel to check permissions for
        :return: Whether the client can send a message or not
        """
        if isinstance(channel, discord.DMChannel):
            return True
        if isinstance(channel, discord.Thread):
            return False
        perms: list = list(iter(channel.permissions_for(channel.guild.me)))
        overwrites: list = list(iter(channel.overwrites_for(channel.guild.me)))  # weird inspection, keep an eye on this
        return (
            all(
                req in perms + overwrites
                for req in [
                    ('send_messages', True),
                    ('read_messages', True),
                    ('read_message_history', True),
                ]
            )
            or ('administrator', True) in perms
        )

    @staticmethod
    async def get_most_common(items: list | tuple) -> Any:
        """
        Get the most common item from a list/tuple

        :param items: The iterable to return the most common item of
        :return: The most common item from the iterable
        """
        return max(set(items), key=items.count)

    @staticmethod
    def get_remaining_keys(dict_: dict, keys: Iterable[str]) -> list[str]:
        """
        Return list(set(dict.keys()) ^ set(keys))

        :param dict_: The dictionary to get the remaining keys from
        :param keys: The keys to perform the XOR operation with
        :return: The remaining keys
        """
        return list(set(dict_.keys()) ^ set(keys))

    @staticmethod
    def regex_get(dict_: dict, pattern: re.Pattern | str, default: Any = None) -> Any:
        """
        Kinda like dict.get, but with regex or __in__

        :param dict_: The dictionary to get the value from
        :param pattern: The pattern to match (The action will be __in__ if it's a string)
        :param default: The default value to return if no match is found
        :return: The value associated with the pattern, or the default value
        """
        compare: Callable = ((lambda k_: bool(pattern.match(k_))) if isinstance(pattern, re.Pattern)
                             else lambda k_: pattern in k_)
        return next((v for k, v in dict_.items() if compare(k)), default)

    @staticmethod
    def get_nested_key(dict_: AnyDict, key: Iterable[str] | str, sep: str = ' ') -> Any:
        """
        Get a nested dictionary key

        :param dict_: The dictionary to get the key from
        :param key: The key to get
        :param sep: The separator to use if key is a string
        :return: The value associated with the key
        """
        if isinstance(key, str):
            key = key.split(sep=sep)

        for k in key:
            if k.endswith("]"):
                index_start = k.index("[")
                index = int(k[index_start + 1:-1])
                dict_ = dict_[index]
            else:
                dict_ = dict_.get(k)

        return dict_

    @staticmethod
    def chunks(iterable: list | tuple, chunk_size: int) -> Generator[list | tuple, None, None]:
        """
        Returns a generator of equally sized chunks from an iterable.
        If the iterable is not evenly divisible by chunk_size, the last chunk will be smaller.
        Useful for displaying a list inside multiple embeds.

        :param iterable: The iterable to chunk
        :param chunk_size: The size of the chunks (list has len 10, chunk_size is 5 -> 2 lists of 5)
        :return: A generator of chunks sized <= chunk_size
        """
        n: int = max(1, chunk_size)
        return (iterable[i:i + n] for i in range(0, len(iterable), n))

    @staticmethod
    def _eval_bool_literal_safe(literal: str) -> str | bool:
        """
        Safely convert a string literal to a boolean, or return the string

        :param literal: The literal to convert
        :return: The converted literal or the literal itself if it's not a boolean
        """
        match literal.lower():
            case 'true' | 't' | 'y' | '1' | 'yes':
                return True
            case 'false' | 'f' | 'n' | '0' | 'no':
                return False
            case _:
                return literal

    @staticmethod
    def parse_repo(repo: Optional[str]) -> Optional[Type[ParsedRepositoryData] | str]:
        """
        Parse an owner/name(/branch)? repo string into :class:`ParsedRepositoryData`

        :param repo: The repo string
        :return: The parsed repo or the repo argument unchanged
        """
        if repo and (match := r.REPOSITORY_NAME_RE.match(repo)):
            return ParsedRepositoryData(**match.groupdict())
        return repo

    @staticmethod
    def get_last_call_from_callstack(frames_back: int = 2) -> str:
        """
        Get the name of a callable in the callstack.
        If the encountered callable is a method, return the name in the "ClassName.method_name" format.

        :param frames_back: The number of frames to go back and get the callable name from
        :return: The callable name
        """
        frame = inspect.stack()[frames_back][0]
        if 'self' in frame.f_locals:
            return f'{frame.f_locals["self"].__class__.__name__}.{frame.f_code.co_name}'
        return frame.f_code.co_name

    @staticmethod
    def release_feed_mention_to_actual(mention: ReleaseFeedItemMention) -> str:
        """
        Convert a release feed mention field to an actual mention

        :param mention: The release feed mention value
        :return: The actual mention
        """
        return f'@{mention}' if isinstance(mention, str) else f'<@&{mention}>'

    @staticmethod
    async def just_run(func: Callable, *args, **kwargs) -> Any:
        """
        Run a function without a care in the world about whether it's async or not

        :param func: The function to run
        :param args: The function's positional arguments
        :param kwargs: The function's keyword arguments
        """

        if asyncio.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        return func(*args, **kwargs)

    @staticmethod
    def github_timestamp_to_international(timestamp: str, y_sep: str = '/', t_sep: str = ':') -> str:
        """
        Convert a GitHub timestamp to a human-readable international timestamp

        :param timestamp: The GitHub timestamp
        :param y_sep: The separator to use between the year, month and day
        :param t_sep: The separator to use between the hour, minute and second
        :return: The international timestamp
        """
        return datetime.datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%SZ').strftime(f'%Y{y_sep}%m{y_sep}%d, %H{t_sep}%M{t_sep}%S')

    @staticmethod
    def advanced_format(template_str: str, source: dict, handlers: tuple[Callable[[str], str] | str, ...] | Callable[[str], str]) -> str:
        """
        Format a string using extended syntax.
        This function formats the string with keys from the dictionary, i.e. {key} will be replaced with source[key].
        It also supports handlers that manipulate the value before it's inserted into the string, which is done
        by passing the handler index in the key, i.e. {0(key)} will be replaced with handlers[0](source[key]).

        :param template_str: The string to format
        :param source: The dictionary to get the keys from
        :param handlers: The handlers to use
        :return: The formatted string
        """
        if not isinstance(handlers, tuple):
            handlers = (handlers,)
        field_handlers: dict[str, int] = {**{f: None for f in [fname for _, fname, _, _ in string.Formatter().parse(template_str) if fname]}}
        for field in filter(lambda f: '(' in f, field_handlers):
            handler_index = int(field.split('(')[0])
            field_handlers[field] = handler_index
        values: dict[str, str] = {
            field: Manager.get_nested_key(source, field) for field in field_handlers if field_handlers[field] is None
        }
        for field, handler_index in field_handlers.items():
            if field not in values:
                handler = handlers[handler_index]
                inner_fetch: str = Manager.get_nested_key(source, field[field.find('(')+1:field.find(')')])
                if isinstance(handler, str) and not inner_fetch:
                    values[field] = Manager.get_nested_key(source, handler)
                elif inspect.isfunction(handler):
                    values[field] = handlers[handler_index](inner_fetch)
                else:
                    values[field] = inner_fetch
        return template_str.format(**values)

    def _setup_db(self) -> None:
        """
        Setup the database connection with ENV vars and a more predictable certificate location.
        """
        self._ca_cert: str = certifi.where()
        self.db_client: AsyncIOMotorClient = AsyncIOMotorClient(self.env.db_connection,
                                                                appname=self.bot_dev_name,
                                                                tls=self.env.db_use_tls,
                                                                tlsCAFile=self._ca_cert,
                                                                tlsAllowInvalidCertificates=False)
        self.db: AsyncIOMotorCollection = getattr(self.db_client, 'store' if self.env.production else 'test')

    def _maybe_set_env_directive(self, name: str, value: str | bool | int | list | dict, overwrite: bool = True) -> bool:
        """
        Optionally add an environment directive (behavior config for environment loading)

        :param name: The name of the env binding
        :param value: The value of the env binding
        :param overwrite: Whether to overwrite an existing directive
        :return: Whether or not the directive was added or not
        """
        if isinstance(value, str):
            value: str | bool = self._eval_bool_literal_safe(value)

        if (directive := name.lower()).startswith('directive_'):
            if (directive := directive.replace('directive_', '')) not in \
                    self.env_directives or (directive in self.env_directives and overwrite):
                self._set_env_directive(directive, value)
                return True
        return False

    def _set_env_directive(self, directive: str, value: bool) -> None:
        self.env_directives[directive] = value

    def _prepare_env(self) -> None:
        """
        Private function meant to be called at the time of instantiating this class,
        loads .env with defaults from data/env_defaults.json into self.env.
        """
        self.env: DictProxy = DictProxy({k: v for k, v in dict(os.environ).items()
                                         if not self._maybe_set_env_directive(k, v)})
        self.env_directives: DictProxy = DictProxy()

        with open('resources/env_defaults.json', 'r', encoding='utf8') as fp:
            env_defaults: dict = json.loads(fp.read())
            for k, v in env_defaults.items():
                k: str
                if not self._maybe_set_env_directive(k, v) and k not in self.env:
                    self.env[k] = v
                    if isinstance(v, str):
                        os.environ[k.upper()] = v
        self.load_dotenv()
        self.bot.logger.info('Environment directives set: %s', '; '.join([f'{k} -> {v}' for k, v in self.env_directives.items()]))

    def _handle_env_binding(self, binding: dotenv.parser.Binding) -> None:
        """
        Handle an environment key->value binding.

        :param binding: The binding to handle
        """
        if self._maybe_set_env_directive(binding.key, binding.value):
            return
        try:
            if self.env_directives.get('eval_literal'):
                if isinstance((parsed := self._eval_bool_literal_safe(binding.value)), bool):
                    self.env[binding.key] = parsed
                else:
                    self.env[binding.key] = (parsed := self.parse_literal(binding.value))
            else:
                self.env[binding.key] = (parsed := binding.value)
            self.bot.logger.info('env[%s] loaded as "%s"', binding.key, type(parsed).__name__)
            return
        except (ValueError, SyntaxError):
            self.env[binding.key] = binding.value
            self.bot.logger.info('env[%s] loaded as "str"', binding.key)

    def load_dotenv(self) -> None:
        """
        Load the .env file (if it exists) into self.env.
        This method's capabilities are largely extended compared to plain dotenv:
            - Directives ("DIRECTIVE_{X}") that modify the behavior of the parser
            - Defaults are loaded from env_defaults.json first, so that .env values take precedence
            - With the "eval_literal" directive active, binding values are parsed with AST during runtime
        """
        if dotenv_path := dotenv.find_dotenv():
            self.bot.logger.info('Found .env file, loading environment variables listed inside of it.')
            with open(dotenv_path, 'r', encoding='utf8') as fp:
                for binding in dotenv.parser.parse_stream(fp):
                    self._handle_env_binding(binding)

    @staticmethod
    def github_to_discord_timestamp(github_timestamp: str) -> str:
        """
        Convert a GitHub-formatted timestamp (%Y-%m-%dT%H:%M:%SZ) to the <t:timestamp> Discord format

        :param github_timestamp: The GitHub timestamp to convert
        :return: The converted timestamp
        """
        return Manager.external_to_discord_timestamp(github_timestamp, "%Y-%m-%dT%H:%M:%SZ")

    _number_re: re.Pattern = re.compile(r'\d+')

    @staticmethod
    def sizeof(object_: object, handlers: Optional[dict] = None) -> int:
        """
        Return the approximate memory footprint of an object and all of its contents.

        Automatically finds the contents of the following builtin containers and
        their subclasses: :class:`tuple`, :class:`list`, :class:`deque`, :class:`dict`,
        :class:`set` and :class:`frozenset`. To search other containers, add handlers to iterate over their contents:

        handlers = {SomeContainerClass: iter,
                    OtherContainerClass: OtherContainerClass.get_elements}
        """
        if handlers is None:
            handlers: dict = {}

        all_handlers: dict = {tuple: iter, list: iter,
                              deque: iter, dict: lambda d: chain.from_iterable(d.items()),
                              set: iter, frozenset: iter}
        all_handlers.update(handlers)
        seen: set = set()

        def _sizeof(_object: object) -> int:
            if id(_object) in seen:
                return 0
            seen.add(id(_object))
            size: int = getsizeof(_object, getsizeof(0))

            for type_, handler in all_handlers.items():
                if isinstance(_object, type_):
                    size += sum(map(_sizeof, handler(_object)))
                    break
            return size

        final_size: int = _sizeof(object_)
        return final_size

    def get_numbers_in_range_in_str(self, string: str, max_: int = 10) -> list[int]:
        """
        Return a list of numbers from str that are < max_

        :param string: The string to search for numbers
        :param max_: The max_ number to include in the returned list
        :return: The list of numbers
        """
        return list(self._number_re.findall(string) | select(lambda ns: int(ns)) | where(lambda n: n <= max_))

    _int_word_conv_map: dict = {
        'zero': 0,
        'one': 1,
        'two': 2,
        'three': 3,
        'four': 4,
        'five': 5,
        'six': 6,
        'seven': 7,
        'eight': 8,
        'nine': 9,
        'ten': 10
    }

    def wtoi(self,
             word: str) -> Optional[int]:
        """
        Word to :class:`int`. I'm sorry.

        :param word: The word to convert
        :return: The converted word or None if invalid
        """
        return self._int_word_conv_map.get(word.casefold())

    def itow(self, _int: int) -> Optional[str]:
        """
        :class:`int` to word. I'm sorry.

        :param _int: The integer to convert
        :return: The converted int or None if invalid
        """
        for k, v in self._int_word_conv_map.items():
            if v == _int:
                return k

    def dict_full_path(self,
                       dict_: AnyDict,
                       key: str,
                       value: Optional[Any] = None) -> Optional[tuple[str, ...]]:
        """
        Get the full path of a dictionary key in the form of a tuple.
        The value is an optional parameter that can be used to determine which key's path to return if many are present.

        :param dict_: The dictionary to which the key belongs
        :param key: The key to get the full path to
        :param value: The optional value for determining if a key is the right one
        :return: None if key not in dict_ or dict_[key] != value if value is not None else the full path to the key
        """
        if hasattr(dict_, 'actual'):
            dict_: dict = dict_.actual

        def _recursive(__prev: tuple = ()) -> Optional[tuple[str, ...]]:
            reduced: dict = self.get_nested_key(dict_, __prev)
            for k, v in reduced.items():
                if k == key and (value is None or (value is not None and v == value)):
                    return *__prev, key
                if isinstance(v, dict):
                    if ret := _recursive((*__prev, k)):
                        return ret

        return _recursive()

    def extract_content_from_codeblock(self, codeblock: str) -> Optional[str]:
        """
        Extract code from the codeblock while retaining indentation.

        :param codeblock: The codeblock to strip
        :return: The code extracted from the codeblock
        """
        if match_ := (
            re.search(r.MULTILINE_CODEBLOCK_RE, codeblock)
            or re.search(r.SINGLE_LINE_CODEBLOCK_RE, codeblock)
        ):
            self.bot.logger.debug('Matched codeblock')
            return match_.group('content').rstrip('\n')
        self.bot.logger.debug("Couldn't match codeblock")

    async def unzip_file(self, zip_path: str, output_dir: str) -> None:
        """
        Unzip a ZIP file to a specified location

        :param zip_path: The location of the ZIP file
        :param output_dir: The output directory to extract ZIP file contents to
        """
        if not os.path.exists(output_dir):
            self.bot.logger.debug('Creating output directory "%s"', output_dir)
            os.mkdir(output_dir)
        with zipfile.ZipFile(zip_path) as _zip:
            self.bot.logger.debug('Extracting zip archive "%s"', zip_path)
            _zip.extractall(output_dir)

    def get_license(self, to_match: str) -> Optional[DictProxy]:
        """
        Get a license matching the query.

        :param to_match: The query to search by
        :return: The best license matched or None if match is less than 80
        """
        best: list[tuple[int, DictProxy]] = []

        for i in list(self.licenses):
            _match1: int = fuzz.token_set_ratio(to_match, i['name'])
            _match2: int = fuzz.token_set_ratio(to_match, i['key'])
            _match3: int = fuzz.token_set_ratio(to_match, i['spdx_id'])
            if any([_match1 > 80, _match2 > 80, _match3 > 80]):
                score: int = sum([_match1, _match2, _match3])
                self.bot.logger.debug('Matched license "%s" with one-attribute confidence >80 from "%s"', i["name"], to_match)
                best.append((score, i))
        if best:
            pick: tuple[int, DictProxy] = max(best, key=lambda s: s[0])
            self.bot.logger.debug('Found {0} matching licenses, picking the best one with score {1}', len(best), pick[0])
            return pick[1]
        self.bot.logger.debug('No matching license found for "%s"', to_match)
        return None

    def load_json(self,
                  name: str,
                  apply_func: Optional[Callable[[str, list | str | int | bool], Any]] = None) -> DictProxy:
        """
        Load a JSON file from the data dir

        :param name: The name of the JSON file
        :param apply_func: The function to apply to all dictionary k->v tuples except when isinstance(v, dict),
               then apply recursion until an actionable value (list | str | int | bool) is found in the node
        :return: The loaded JSON wrapped in DictProxy
        """
        to_load = f'./resources/{name.lower()}.json' if name[-5:] != '.json' else ''
        with open(to_load, 'r', encoding='utf8') as fp:
            data: dict | list = json.load(fp)
        proxy: DictProxy = DictProxy(data)

        if apply_func:
            self.bot.logger.debug('Applying func %s', apply_func.__name__)

            def _recursive(node: AnyDict) -> None:
                for k, v in node.items():
                    if isinstance(v, (dict, DictProxy)):
                        _recursive(v)
                    else:
                        node[k] = apply_func(k, v)

            _recursive(proxy)
        return proxy

    async def get_link_reference(self,
                                 ctx: 'GitBotContext') -> Optional[GitCommandData]:
        """
        Get the command data required for invocation from a context

        :param ctx: The context to search for links, and then optionally exchange for command data
        :return: The command data requested
        """
        combos: tuple[tuple[re.Pattern, tuple | str], ...] = ((r.GITHUB_PULL_REQUEST_URL_RE, 'pr'),
                                                              (r.GITHUB_ISSUE_URL_RE, 'issue'),
                                                              (r.GITHUB_PULL_REQUESTS_PLAIN_URL_RE, 'repo pulls'),
                                                              (r.GITHUB_ISSUES_PLAIN_URL_RE, 'repo issues'),
                                                              (r.GITHUB_COMMIT_URL_RE, 'commit'),
                                                              (r.GITHUB_REPO_TREE_RE, 'repo-files-two-arg'),
                                                              (r.GITHUB_REPO_URL_RE, 'repo info'),
                                                              (r.GITHUB_USER_ORG_URL_RE, ('user info', 'org info')))
        for pattern, command_name in combos:
            if match := pattern.search(ctx.message.content):
                if isinstance(command_name, str):
                    command: commands.Command = ctx.bot.get_command(command_name)
                    kwargs: dict = dict(zip(command.clean_params.keys(), match.groups()))
                else:
                    command: tuple[commands.Command, ...] = tuple(ctx.bot.get_command(name) for name in command_name)
                    kwargs: tuple[dict, ...] = tuple(dict(zip(cmd.clean_params.keys(),
                                                              match.groups())) for cmd in command)
                return GitCommandData(command, kwargs)
        self.bot.logger.debug('No match found for "%s"', ctx.message.content)

    @staticmethod
    def construct_gravatar_url(email: str, size: int = 512, default: Optional[str] = None) -> str:
        """
        Construct a valid Gravatar URL with optional size and default parameters

        :param email: The email to fetch the Gravatar for
        :param size: The size of the Gravatar, default is 512
        :param default: The URL to default to if the email address doesn't have a Gravatar
        :return: The Gravatar URL constructed with the arguments
        """
        url: str = f'https://www.gravatar.com/avatar/{hashlib.md5(email.encode("utf8").lower()).hexdigest()}?s={size}'
        if default:
            url += f'&d={quote_plus(default)}'
        return url

    async def ensure_http_status(self,
                                 url: str,
                                 code: int = 200,
                                 method: str = 'GET',
                                 alt: Any = None,
                                 **kwargs) -> Any:
        """
        Ensure that an HTTP request returned a particular status, if not, return the alt parameter

        :param url: The URL to request
        :param code: The wanted status code
        :param method: The method of the request
        :param alt: The value to return if the status code is different from the code parameter
        :return: The URL if the statuses match, or the alt parameter if not
        """
        if (await self.git.session.request(method=method, url=url, **kwargs)).status == code:
            return url
        return alt

    def validate_index(self, number: str| int, items: list[AnyDict]) -> Optional[dict]:
        """
        Validate an index against a list of indexed dicts

        :param number: The number to safely convert, then check
        :param items: The list of indexed dicts to check against
        :return: The dict matching the index
        """
        if isinstance(number, str):
            if number.startswith('#'):
                number: str = number[1:]
            try:
                number: int = int(number)
            except (TypeError, ValueError):
                return None
        if matched := self.opt([i for i in items if i['number'] == number], 0):
            return matched

    async def reverse(self, seq: Optional[Reversible]) -> Optional[Iterable]:
        """
        Reverse function with a None failsafe and recasting to the original type

        :param seq: The sequence to reverse
        :return: The reversed sequence if not None, else None
        """
        if seq:
            return type(seq)(reversed(seq))  # noqa
        self.bot.logger.debug('Sequence is None')

    def readdir(self, path: str, ext: Optional[str | list | tuple] = None, **kwargs) -> Optional[DirProxy]:
        """
        Read a directory and return a file-mapping object

        :param path: The directory path
        :param ext: The extensions to include, None for all
        :return: The mapped directory
        """
        if os.path.isdir(path):
            return DirProxy(path=path, ext=ext, **kwargs)
        self.bot.logger.debug('Not a directory: "%s"', path)

    @normalize_identity(context_resource='guild')
    async def get_autoconv_config(self,
                                  _id: Identity,
                                  did_exist: bool = False) -> Type[AutomaticConversionSettings] | tuple[AutomaticConversionSettings,
                                                                                                        bool]:
        """
        Get the configured permission for automatic conversion from messages (links, snippets, etc.)

        :param _id: The guild ID to get the permission value for
        :param did_exist: If to return whether if the guild document existed, or if the value is default
        :return: The permission value, by default env[AUTOCONV_DEFAULT]
        """
        _did_exist: bool = False

        if cached := self.autoconv_cache.get(_id):
            _did_exist: bool = True
            permission: AutomaticConversionSettings = cached
            self.bot.logger.debug('Returning cached value for identity "%d"', _id)
        else:
            stored: Optional[GitBotGuild] = await self.db.guilds.find_one({'_id': _id})
            if stored:
                permission: AutomaticConversionSettings = stored.get('autoconv', self.env.autoconv_default)
                _did_exist: bool = True
            else:
                permission: AutomaticConversionSettings = self.env.autoconv_default
            self.autoconv_cache[_id] = permission
        return permission if not did_exist else (permission, _did_exist)

    @normalize_identity()
    async def get_locale(self, _id: Identity) -> DictProxy:
        """
        Get the locale associated with a user, defaults to the master locale

        :param _id: The user object/ID to get the locale for
        :return: The locale associated with the user
        """
        locale: LocaleName = self.locale.master.meta.name
        if cached := self.locale_cache.get(_id):
            locale: LocaleName = cached
            self.bot.logger.debug('Returning cached value for identity "%d"', _id)
        elif stored := await self.db.users.getitem(_id, 'locale'):
            locale: str = stored
        try:
            self.locale_cache[_id] = locale
            return getattr(self.l, locale)
        except AttributeError:
            return self.locale.master

    def get_by_key_from_sequence(self,
                                 seq: DictSequence,
                                 key: str,
                                 value: Any,
                                 multiple: bool = False,
                                 unpack: bool = False) -> Optional[AnyDict | list[AnyDict]]:
        """
        Get a dictionary from an iterable, where d[key] == value

        :param seq: The sequence of dicts
        :param key: The key to check
        :param value: The wanted value
        :param multiple: Whether to search for multiple valid dicts, time complexity is always O(n) with this flag
        :param unpack: Whether the comparison op should be __in__ or __eq__
        :return: The dictionary with the matching value, if any
        """
        matching: list = []
        if len((_key := key.split())) > 1:
            key: list = _key
        for d in seq:
            if isinstance(key, str):
                if (key in d) and (d[key] == value) if not unpack else (d[key] in value):
                    if multiple:
                        matching.append(d)
                    else:
                        return d
            elif (self.get_nested_key(d, key) == value) if not unpack else (self.get_nested_key(d, key) in value):
                if multiple:
                    matching.append(d)
                else:
                    return d
        return matching

    def populate_generic_numbered_resource(self,
                                           resource: dict,
                                           fmt_str: Optional[str] = None,
                                           **values: int) -> dict[str, str] | str:
        """
        The GitBot locale is a bit special, as it has a lot of numbered resources.
        Generic numbered resources are sub-dictionaries of locale values; they contain 3 or more keys:
        - `plural`: The plural formatting string (n > 1)
        - `singular`: The singular formatting string (n == 1)
        - `no_(...)`: The formatting string for n == 0
        This function will populate a generic numbered resource, and return the formatted string if provided

        :param resource: The resource to populate
        :param fmt_str: The formatting string to use
        :param values: The values to use for the formatting string
        :return: The formatted string, or the resource
        """
        populated: dict[str, str] = {}
        for rk, rv in resource.items():
            for vn, v in values.items():
                if isinstance(rv, dict):
                    if rk == vn:
                        res: str = resource[rk]['plural'].format(v)
                        if v < 2:
                            res: str = resource[rk]['singular'] if v == 1 else self.regex_get(resource[rk], 'no_')
                        populated[rk] = res
                else:
                    populated[rk] = rv
        return fmt_str.format(**populated) if fmt_str else populated

    def option_display_list_format(self, options: dict[str, str] | list[str], style: str = 'pixel') -> str:
        """
        Utility method to construct a string representation of a numbered list from :class:`dict` or :class:`list`

        :param options: The options to build the list from
        :param style: The style of digits to use (emoji.json["digits"][style])
        :return: The created list string
        """
        resource: dict = self.e['digits'][style]
        if isinstance(options, dict):
            return '\n'.join([f"{resource[self.itow(i+1)]}** {kv[0].capitalize()}** {kv[1]}"
                              for i, kv in enumerate(options.items())])
        return '\n'.join([f"{resource[self.itow(i+1)]} - {v}" for i, v in enumerate(options)])

    def get_missing_keys_for_locale(self, locale: str) -> Optional[tuple[list[str], DictProxy, bool]]:
        """
        Get keys missing from a locale in comparison to the master locale

        :param locale: Any meta attribute of the locale
        :return: The missing keys for the locale and the confidence of the attribute match
        """
        if locale_data := self.get_locale_meta_by_attribute(locale):
            missing: list = list(
                {item for item in self._missing_locale_keys[locale_data[0]['name']] if item is not None})
            missing.sort(key=lambda path: len(path) * sum(map(len, path)))
            return missing, locale_data[0], locale_data[1]

    def get_locale_meta_by_attribute(self, attribute: str) -> Optional[tuple[DictProxy, bool]]:
        """
        Get a locale from a potentially malformed attribute.
        If there isn't a match above 80, returns None

        :param attribute: The attribute to match
        :return: The locale or None if not matched
        """
        for locale in self.locale.languages:
            for lv in locale.values():
                match_: int = fuzz.token_set_ratio(attribute, lv)
                if lv == attribute or match_ > 80:
                    return locale, match_ == 100

    def get_all_dict_paths(self, d: dict, __path: list[str] | None = None) -> list[list[str]]:
        """
        Get all paths in a dictionary

        :param d: The dictionary to get the paths from
        :return: A list of paths
        """
        __path: list = [] if __path is None else __path
        paths: list = []
        for k, v in d.items():
            if isinstance(v, dict):
                paths.extend(self.get_all_dict_paths(v, __path + [k]))
            else:
                paths.append(__path + [k])
        return paths

    def get_localization_percentage(self, locale: str) -> float:
        # TODO some locale items are not supposed to be translated and others sound the same in the target language, this feature is not ready yet
        """
        Get the localization percentage of a locale

        :param locale: The locale to get the percentage for
        :return: The percentage
        """
        if not (locale := getattr(self.l, locale, None)):
            return
        if self.localization_percentages.get(locale.meta['name']) is not None:
            return self.localization_percentages[locale.meta['name']]
        ml_copy: dict = deepcopy(self.locale.master.actual)
        ml_paths: list = self.get_all_dict_paths(ml_copy)
        non_localized: int = sum(
            1
            for k in ml_paths
            if self.get_nested_key(locale, k) == self.get_nested_key(ml_copy, k)
        )
        result: float = round((1 - (non_localized / len(ml_paths))) * 100, 2)
        self.localization_percentages[locale.meta['name']] = result
        return result

    def fix_dict(self, dict_: AnyDict, ref_: AnyDict, locale: bool = False) -> AnyDict:
        """
        Add missing keys to the dictionary

        :param dict_: The dictionary to fix
        :param ref_: The dictionary to refer to when getting the keys
        :param locale: Whether the dictionaries are locales (logging)
        :return: The fixed dict
        """
        def recursively_fix(node: AnyDict, ref: AnyDict) -> AnyDict:
            for k, v in ref.items():
                if k not in node:
                    if locale:
                        self._missing_locale_keys[dict_.meta.name].append(path := self.dict_full_path(ref_, k, v))
                        self.bot.logger.warning('Missing key "%s" patched in locale "%s"',
                                                ' -> '.join(path) if path else k, dict_.meta.name)
                    node[k] = v if not isinstance(v, dict) else DictProxy(v)
            for k, v in node.items():
                if isinstance(v, (DictProxy, dict)):
                    try:
                        node[k] = recursively_fix(v, ref[k])
                    except KeyError:
                        pass
            return node

        return recursively_fix(dict_, ref_)

    def __fix_missing_locales(self):
        """
        Fill in locales with missing keys with the Master locale
        """
        for locale in self.l:
            if locale != self.locale.master and 'meta' in locale:
                setattr(self.l, locale.meta.name, self.fix_dict(locale, self.locale.master, locale=True))

    def _replace_emoji(self, match_: re.Match, default: str = '**[?]**') -> str:
        """
        Generate a replacement string from a match object's emoji_name variable with a Manager emoji

        :param match_: The match to generate the replacement for
        :return: The replacement string
        """
        if group := match_['emoji_name']:
            return self.e.get(group, default)
        return match_.string

    def __preprocess_locale_emojis(self):
        """
        Preprocess locales by replacing {emoji_[x]} with self.e.[x] (Emoji formatting)
        """

        def _preprocess(node: AnyDict) -> None:
            for k, v in node.items():
                if isinstance(v, (DictProxy, dict)):
                    _preprocess(v)
                elif isinstance(v, str):
                    if '{emoji_' in v:
                        node[k] = r.LOCALE_EMOJI_TEMPLATE_RE.sub(self._replace_emoji, v)
                elif isinstance(v, list):
                    for i, item in enumerate(v):
                        if isinstance(item, str):
                            if '{emoji_' in item:
                                v[i] = r.LOCALE_EMOJI_TEMPLATE_RE.sub(self._replace_emoji, item)
                        elif isinstance(item, (DictProxy, dict)):
                            _preprocess(item)
                    node[k] = v

        for locale in self.l:
            _preprocess(locale)

    def __preprocess_localization_percentages(self):
        """
        Preprocess localization percentages
        """
        for locale in self.l:
            if locale != self.locale.master:
                pc: float = self.get_localization_percentage(locale.meta.name)
                self.localization_percentages[locale.meta.name] = pc
                self.bot.logger.info('Locale is %s% localized', pc)

    def fmt(self, ctx: 'GitBotContext'):
        """
        Instantiate a new Formatter object. Meant for binding to Context.

        :param ctx: The command invocation Context
        :return: The Formatter object created with the Context
        """
        self_: Manager = self



        class _Formatter:
            def __init__(self, ctx_: 'GitBotContext'):
                self.ctx: 'GitBotContext' = ctx_
                self.prefix: str = ''

            def __call__(self, resource: tuple | str | list, /, *args, **kwargs) -> str:
                skip_prefix: bool = False
                if resource.startswith('!'):  # skip-prefix behavior if the resource has a preceding exclamation mark
                    skip_prefix: bool = True
                    resource: str = resource[1:]
                resource: str = ((self.prefix if not skip_prefix else '') + resource
                                 if not resource.startswith(self.prefix) else resource)
                try:
                    return self_.get_nested_key(self.ctx.l, resource).format(*args, **kwargs)
                except IndexError:
                    return self_.get_nested_key(self_.locale.master, resource).format(*args)

            def set_prefix(self, prefix: str, absolute: bool = True) -> None:
                if prefix.startswith('+'):
                    self_.bot.logger.debug('Prefix mode is append, stripping op sign in \'%s\'', prefix)
                    prefix: str = prefix[1:]
                    absolute: bool = False
                self.prefix: str = (
                    f'{prefix.strip()} '
                    if absolute
                    else self.prefix + prefix.strip() + ' '
                )
                self_.bot.logger.debug('Locale formatting prefix set to \'%s\' in '
                                       '\'%s\'', self.prefix.strip(), self_.get_last_call_from_callstack())


        return _Formatter(ctx)
