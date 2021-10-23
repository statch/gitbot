import re
import os
import ast
import json
import dotenv
import discord
import zipfile
import os.path
import inspect
import hashlib
import aiohttp
import certifi
import operator
import datetime
import functools
import dotenv.parser
from sys import getsizeof
from itertools import chain
from fuzzywuzzy import fuzz
from collections import deque
from lib.utils import regex as r
from colorama import Style, Fore
from discord.ext import commands
from urllib.parse import quote_plus
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection  # noqa
from lib.utils.decorators import normalize_identity
from typing import Optional, Union, Callable, Any, Reversible, Iterable
from lib.typehints import DictSequence, AnyDict, Identity, GitBotGuild, AutomaticConversion, LocaleName
from lib.structs import (DirProxy, DictProxy,
                         GitCommandData, UserCollection,
                         TypedCache, SelfHashingCache,
                         CacheSchema, ParsedRepositoryData)


class Manager:
    """
    A class containing database, locale and utility functions

    :param github: The GitHubAPI instance to use
    :type github: :class:`lib.net.github.api.GitHubAPI`
    """

    def __init__(self, github):
        self.git = github
        self.ses: aiohttp.ClientSession = self.git.ses
        self._prepare_env()
        self.bot_dev_name: str = f'gitbot ({"production" if self.env.production else "preview"})'
        self.debug_mode: bool = (not self.env.production) or self.env.get('debug', False)
        self._setup_db()
        self.l: DirProxy = self.readdir('resources/locale/', '.json', exclude='index.json')
        self.e: DictProxy = self.load_json('emoji')
        self.c: DictProxy = self.load_json('colors', lambda k, v: v if not (isinstance(v, str)
                                                                            and v.startswith('#')) else int(v[1:], 16))
        self.i: DictProxy = self.load_json('images')
        self.locale: DictProxy = self.load_json('locale/index')
        self.licenses: DictProxy = self.load_json('licenses')
        self.carbon_attachment_cache: SelfHashingCache = SelfHashingCache(max_age=60 * 60)
        self.autoconv_cache: TypedCache = TypedCache(CacheSchema(key=int, value=dict))
        self.locale_cache: TypedCache = TypedCache(CacheSchema(key=int, value=str), maxsize=256)
        self.loc_cache: TypedCache = TypedCache(CacheSchema(key=str, value=dict), maxsize=64, max_age=60 * 30)
        self.locale.master = getattr(self.l, str(self.locale.master))
        self.db.users = UserCollection(self.db.users, self.git, self)
        self._missing_locale_keys: dict = {l_['name']: [] for l_ in self.locale['languages']}
        self.__fix_missing_locales()
        self.__preprocess_locale_emojis()

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

    def _eval_bool_literal_safe(self, literal: str) -> Union[str, bool]:
        """
        Safely convert a string literal to a boolean, or return the string

        :param literal: The literal to convert
        :return: The converted literal or the literal itself if it's not a boolean
        """

        if (literal_ := literal.lower()) == 'true':
            return True
        elif literal_ == 'false':
            return False
        return literal

    def _set_env_directive(self, name: str, value: Union[str, bool, int, list, dict], overwrite: bool = True) -> bool:
        """
        Optionally add an environment directive (behavior config for environment loading)

        :param name: The name of the env binding
        :param value: The value of the env binding
        :param overwrite: Whether to overwrite an existing directive
        :return: Whether or not the directive was added or not
        """

        if isinstance(value, str):
            value: Union[str, bool] = self._eval_bool_literal_safe(value)

        if (directive := name.lower()).startswith('directive_'):
            if (directive := directive.replace('directive_', '')) not in \
                    self.env_directives or (directive in self.env_directives and overwrite):
                self.env_directives[directive] = value
                self.log(f'Directive set: {directive}->{value}', f'core-{Fore.LIGHTYELLOW_EX}env')
                return True
        return False

    def _prepare_env(self) -> None:
        """
        Private function meant to be called at the time of instantiating this class,
        loads .env with defaults from data/env_defaults.json into self.env.
        """

        self.env: DictProxy = DictProxy({k: v for k, v in dict(os.environ).items()
                                         if not self._set_env_directive(k, v)})
        self.env_directives: DictProxy = DictProxy()

        with open('resources/env_defaults.json', 'r') as fp:
            env_defaults: dict = json.loads(fp.read())
            for k, v in env_defaults.items():
                if not self._set_env_directive(k, v) and k not in self.env:
                    self.env[k] = v
        self.load_dotenv()

    def parse_repo(self, repo: Optional[str]) -> Optional[Union[ParsedRepositoryData, str]]:
        """
        Parse a owner/name(/branch)? repo string into :class:`ParsedRepositoryData`

        :param repo: The repo string
        :return: The parsed repo or the repo argument unchanged
        """

        if repo and (match := r.REPOSITORY_INPUT_RE.match(repo)):
            return ParsedRepositoryData(**match.groupdict())
        return repo

    def _handle_env_binding(self, binding: dotenv.parser.Binding) -> None:
        """
        Handle an environment key->value binding.

        :param binding: The binding to handle
        """

        if not self._set_env_directive(binding.key, binding.value):
            try:
                if self.env_directives.get('eval_literal'):
                    if isinstance((parsed := self._eval_bool_literal_safe(binding.value)), bool):
                        self.env[binding.key] = parsed
                    else:
                        self.env[binding.key] = (parsed := self.parse_literal(binding.value))
                    self.log(f'Loaded as \'{type(parsed).__name__}\': {binding.key}', f'core-{Fore.LIGHTYELLOW_EX}env')
                else:
                    self.env[binding.key] = binding.value
                    self.log(f'Loaded as \'str\': {binding.key}', f'core-{Fore.LIGHTYELLOW_EX}env')
                return
            except (ValueError, SyntaxError):
                self.env[binding.key] = binding.value
                self.log(f'Loaded as \'str\': {binding.key}', f'core-{Fore.LIGHTYELLOW_EX}env')

    def load_dotenv(self) -> None:
        """
        Load the .env file (if it exists) into self.env.
        This method's capabilities are largely extended compared to plain dotenv:
            - Directives ("DIRECTIVE_{X}") that modify the behavior of the parser
            - Defaults are loaded from env_defaults.json first, so that .env values take precedence
            - With the "eval_literal" directive active, binding values are parsed with AST during runtime
        """

        dotenv_path: str = dotenv.find_dotenv()
        if dotenv_path:
            self.log('Found .env file, loading environment variables listed inside of it.',
                     f'core-{Fore.LIGHTYELLOW_EX}env')
            with open(dotenv_path, 'r') as fp:
                for binding in dotenv.parser.parse_stream(fp):
                    self._handle_env_binding(binding)

    def parse_literal(self, literal: str) -> Union[str, bytes, int, set, dict, tuple, list, bool, float, None]:
        """
        Parse a literal into a Python object

        :param literal: The literal to parse
        :raises ValueError, SyntaxError: If the value is malformed, then ValueError or SyntaxError is raised
        :return: The parsed literal (an object)
        """

        return ast.literal_eval(literal)

    def get_closest_match_from_iterable(self, to_match: str, iterable: Iterable[str]) -> str:
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

    def pascal_to_snake_case(self, string: str) -> str:
        """
        Convert a PascalCase string to snake_case

        :param string: The string to convert
        :return: The converted string
        """

        return r.PASCAL_CASE_NAME_RE.sub('_', string).lower()

    def to_github_hyperlink(self, name: str, codeblock: bool = False) -> str:
        """
        Return f"[{name}](GITHUB_URL)"

        :param name: The GitHub name to embed in the hyperlink
        :param codeblock: Whether to wrap the hyperlink with backticks
        :return: The created hyperlink
        """

        return (f'[{name}](https://github.com/{name.lower()})' if not codeblock
                else f'[`{name}`](https://github.com/{name.lower()})')

    def truncate(self, string: str, length: int, ending: str = '...', full_word: bool = False) -> str:
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

    def external_to_discord_timestamp(self, timestamp: str, ts_format: str) -> str:
        """
        Convert an external timestamp to the <t:timestamp> Discord format

        :param timestamp: The timestamp
        :param ts_format: The format of the timestamp
        :return: The converted timestamp
        """

        return f'<t:{int(datetime.datetime.strptime(timestamp, ts_format).timestamp())}>'

    def github_to_discord_timestamp(self, github_timestamp: str) -> str:
        """
        Convert a GitHub-formatted timestamp (%Y-%m-%dT%H:%M:%SZ) to the <t:timestamp> Discord format

        :param github_timestamp: The GitHub timestamp to convert
        :return: The converted timestamp
        """

        return self.external_to_discord_timestamp(github_timestamp, "%Y-%m-%dT%H:%M:%SZ")

    _number_re: re.Pattern = re.compile(r'\d+')

    def get_numbers_in_range_in_str(self, string: str, max_: int = 10) -> list[int]:
        return [int(m) for m in self._number_re.findall(string) if int(m) <= max_]

    def log(self,
            message: str,
            category: str = 'core',
            bracket_color: Fore = Fore.LIGHTMAGENTA_EX,
            category_color: Fore = Fore.MAGENTA,
            message_color: Fore = Fore.LIGHTWHITE_EX) -> None:
        """
        Colorful logging function because why not.

        :param message: The message to log
        :param category: The text in brackets
        :param bracket_color: The color of the brackets
        :param category_color: The color of the text in the brackets
        :param message_color: The color of the message
        """

        print(
            f'{bracket_color}[{category_color}{category}{bracket_color}]: {Style.RESET_ALL}{message_color}{message}'
            f'{Style.RESET_ALL}')

    def get_last_call_from_callstack(self, frames_back: int = 2) -> str:
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

    def debug(self, message: str, message_color: Fore = Fore.LIGHTWHITE_EX) -> None:
        """
        A special variant of :meth:`Manager.log` that sets the
        category name as the name of the outer function (the caller)
        and only fires if the ENV[PRODUCTION] value is False.

        :param message: The message to log to the console
        :param message_color: The optional message color override
        """

        if self.debug_mode:
            self.log(message,
                     f'debug-{Fore.LIGHTYELLOW_EX}{self.get_last_call_from_callstack()}{Style.RESET_ALL}',
                     Fore.CYAN, Fore.LIGHTCYAN_EX, message_color)

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

    def sizeof(self, object_: object, handlers: Optional[dict] = None, verbose: bool = False) -> int:
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

            if verbose:
                self.log(
                    message=f'{hex(id(object_))}[{hex(id(_object))}]: {size} bytes | type: {type(_object).__name__}',
                    category=f'debug-{Fore.LIGHTYELLOW_EX}sizeof[{Fore.LIGHTRED_EX}r{Style.RESET_ALL}]')

            for type_, handler in all_handlers.items():
                if isinstance(_object, type_):
                    size += sum(map(_sizeof, handler(_object)))
                    break
            return size

        final_size: int = _sizeof(object_)
        if verbose:
            self.log(message=f'{hex(id(object_))}: {final_size} bytes | type: {type(object_).__name__}',
                     category=f'debug-{Fore.LIGHTYELLOW_EX}sizeof[{Fore.LIGHTGREEN_EX}f{Style.RESET_ALL}]')
        return final_size

    def opt(self, obj: Any, op: Union[Callable, str, int], /, *args, **kwargs) -> Any:
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

        match_: re.Match = (re.search(r.MULTILINE_CODEBLOCK_RE, codeblock) or
                            re.search(r.SINGLE_LINE_CODEBLOCK_RE, codeblock))
        if match_:
            self.debug('Matched codeblock')
            return match_.group('content').rstrip('\n')
        self.debug("Couldn't match codeblock")

    async def unzip_file(self, zip_path: str, output_dir: str) -> None:
        """
        Unzip a ZIP file to a specified location

        :param zip_path: The location of the ZIP file
        :param output_dir: The output directory to extract ZIP file contents to
        """

        if not os.path.exists(output_dir):
            self.debug(f'Creating output directory "{output_dir}"')
            os.mkdir(output_dir)
        with zipfile.ZipFile(zip_path, 'r') as _zip:
            self.debug(f'Extracting zip archive "{zip_path}"')
            _zip.extractall(output_dir)

    def correlate_license(self, to_match: str) -> Optional[DictProxy]:
        """
        Get a license matching the query.

        :param to_match: The query to search by
        :return: The license matched or None if match is less than 80
        """

        for i in list(self.licenses):
            match = fuzz.token_set_ratio(to_match, i['name'])
            match1 = fuzz.token_set_ratio(to_match, i['key'])
            match2 = fuzz.token_set_ratio(to_match, i['spdx_id'])
            if any([match > 80, match1 > 80, match2 > 80]):
                self.debug(f'Matched license "{i["name"]}" with confidence >80 from "{to_match}"')
                return i
        self.debug(f'No matching license found for "{to_match}"')
        return None

    def load_json(self,
                  name: str,
                  apply_func: Optional[Callable[[str, Union[list, str, int, bool]], Any]] = None) -> DictProxy:
        """
        Load a JSON file from the data dir

        :param name: The name of the JSON file
        :param apply_func: The function to apply to all dictionary k->v tuples except when isinstance(v, dict),
               then apply recursion until an actionable value (Union[list, str, int, bool]) is found in the node
        :return: The loaded JSON wrapped in DictProxy
        """

        to_load = './resources/' + str(name).lower() + '.json' if name[-5:] != '.json' else ''
        with open(to_load, 'r') as fp:
            data: Union[dict, list] = json.load(fp)
        proxy: DictProxy = DictProxy(data)

        if apply_func:
            self.debug(f'Applying func {apply_func.__name__}')

            def _recursive(node: AnyDict) -> None:
                for k, v in node.items():
                    if isinstance(v, (dict, DictProxy)):
                        _recursive(v)
                    else:
                        node[k] = apply_func(k, v)

            _recursive(proxy)
        return proxy

    async def verify_send_perms(self, channel: discord.TextChannel) -> bool:
        """
        Check if the client can comfortably send a message to a channel

        :param channel: The channel to check permissions for
        :return: Whether the client can send a message or not
        """

        if isinstance(channel, discord.DMChannel):
            return True
        perms: list = list(iter(channel.permissions_for(channel.guild.me)))
        overwrites: list = list(iter(channel.overwrites_for(channel.guild.me)))
        if all(req in perms + overwrites for req in [("send_messages", True),
                                                     ("read_messages", True),
                                                     ("read_message_history", True)]) \
                or ("administrator", True) in perms:
            return True
        return False

    async def get_link_reference(self,
                                 ctx: commands.Context) -> Optional[Union[GitCommandData, tuple[GitCommandData, ...]]]:
        """
        Get the command data required for invocation from a context

        :param ctx: The context to search for links, and then optionally exchange for command data
        :return: The command data requested
        """

        combos: tuple[tuple[re.Pattern, Union[tuple, str]], ...] = ((r.PR_RE, 'pr'),
                                                                    (r.ISSUE_RE, 'issue'),
                                                                    (r.PULLS_PLAIN_RE, 'repo pulls'),
                                                                    (r.ISSUES_PLAIN_RE, 'repo issues'),
                                                                    (r.COMMIT_URL_RE, 'commit'),
                                                                    (r.REPO_RE, 'repo info'),
                                                                    (r.USER_ORG_RE, ('user info', 'org info')))
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
        self.debug(f'No match found for "{ctx.message.content}"')

    async def get_most_common(self, items: Union[list, tuple]) -> Any:
        """
        Get the most common item from a list/tuple

        :param items: The iterable to return the most common item of
        :return: The most common item from the iterable
        """

        return max(set(items), key=items.count)

    def construct_gravatar_url(self, email: str, size: int = 512, default: Optional[str] = None) -> str:
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

        if (await self.ses.request(method=method, url=url, **kwargs)).status == code:
            return url
        return alt

    async def validate_index(self, number: str, items: list[AnyDict]) -> Optional[dict]:
        """
        Validate an index against a list of indexed dicts

        :param number: The number to safely convert, then check
        :param items: The list of indexed dicts to check against
        :return: The dict matching the index
        """

        if number.startswith('#'):
            number: str = number[1:]
        try:
            number: int = int(number)
        except (TypeError, ValueError):
            return None
        matched = self.opt([i for i in items if i['number'] == number], 0)
        if matched:
            return matched

    async def reverse(self, seq: Optional[Reversible]) -> Optional[Iterable]:
        """
        Reverse function with a None failsafe and recasting to the original type

        :param seq: The sequence to reverse
        :return: The reversed sequence if not None, else None
        """

        if seq:
            return type(seq)(reversed(seq))  # noqa
        self.debug('Sequence is None')

    def readdir(self, path: str, ext: Optional[Union[str, list, tuple]] = None, **kwargs) -> Optional[DirProxy]:
        """
        Read a directory and return a file-mapping object

        :param path: The directory path
        :param ext: The extensions to include, None for all
        :return: The mapped directory
        """

        if os.path.isdir(path):
            return DirProxy(path=path, ext=ext, **kwargs)
        self.debug(f'Not a directory: "{path}"')

    async def enrich_context(self, ctx: commands.Context) -> commands.Context:
        """
        Bind useful attributes to the passed context object

        :param ctx: The context object to bind additional attributes to
        :return: The context object (With new attributes bound)
        """

        ctx.__nocache__ = False
        ctx.__autoinvoked__ = False
        ctx.info = functools.partial(self.send_info, ctx)
        ctx.err = functools.partial(self.send_error, ctx)
        ctx.success = functools.partial(self.send_success, ctx)
        ctx.fmt = self.fmt(ctx)
        ctx.l = await self.get_locale(ctx)  # noqa
        return ctx

    async def send_error(self, ctx: commands.Context, msg: str, **kwargs) -> discord.Message:
        """
        Context.send() with an emoji slapped in front ;-; (!)

        :param ctx: The command invocation context
        :param msg: The message content
        :param kwargs: ctx.send keyword arguments
        """

        return await ctx.send(f'{self.e.err}  {msg}', **kwargs)

    async def send_success(self, ctx: commands.Context, msg: str, **kwargs) -> discord.Message:
        """
        Context.send() with an emoji slapped in front ;-; (checkmark)

        :param ctx: The command invocation context
        :param msg: The message content
        :param kwargs: ctx.send keyword arguments
        """

        return await ctx.send(f'{self.e.checkmark}  {msg}', **kwargs)

    async def send_info(self, ctx: commands.Context, msg: str, **kwargs) -> discord.Message:
        """
        Context.send() with an emoji slapped in front ;-; (github)

        :param ctx: The command invocation context
        :param msg: The message content
        :param kwargs: ctx.send keyword arguments
        """

        return await ctx.send(f'{self.e.github}  {msg}', **kwargs)

    @normalize_identity(context_resource='guild')
    async def get_autoconv_config(self,
                                  _id: Identity,
                                  did_exist: bool = False) -> Union[AutomaticConversion,
                                                                    tuple[AutomaticConversion, bool]]:
        """
        Get the configured permission for automatic conversion from messages (links, snippets, etc.)

        :param _id: The guild ID to get the permission value for
        :param did_exist: If to return whether if the guild document existed, or if the value is default
        :return: The permission value, by default env[AUTOCONV_DEFAULT]
        """

        _did_exist: bool = False

        if cached := self.autoconv_cache.get(_id):
            _did_exist: bool = True
            permission: AutomaticConversion = cached
            self.debug(f'Returning cached value for identity "{_id}"')
        else:
            stored: Optional[GitBotGuild] = await self.db.guilds.find_one({'_id': _id})
            if stored:
                permission: AutomaticConversion = stored.get('autoconv', self.env.autoconv_default)
                _did_exist: bool = True
            else:
                permission: AutomaticConversion = self.env.autoconv_default
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
            self.debug(f'Returning cached value for identity "{_id}"')
        else:
            if stored := await self.db.users.getitem(_id, 'locale'):
                locale: str = stored
        try:
            self.locale_cache[_id] = locale
            return getattr(self.l, locale)
        except AttributeError:
            return self.locale.master

    def get_nested_key(self, dict_: AnyDict, key: Union[Iterable[str], str]) -> Any:
        """
        Get a nested dictionary key

        :param dict_: The dictionary to get the key from
        :param key: The key to get
        :return: The value associated with the key
        """

        return functools.reduce(operator.getitem, key if not isinstance(key, str) else key.split(), dict_)

    def get_by_key_from_sequence(self,
                                 seq: DictSequence,
                                 key: str,
                                 value: Any,
                                 multiple: bool = False,
                                 unpack: bool = False) -> Optional[Union[AnyDict, list[AnyDict]]]:
        """
        Get a dictionary from an iterable, where d[key] == value

        :param seq: The sequence of dicts
        :param key: The key to check
        :param value: The wanted value
        :param multiple: Whether to search for multiple valid dicts, time complexity is always O(n) with this flag
        :return: The dictionary with the matching value, if any
        """

        matching: list = []
        if len((_key := key.split())) > 1:
            key: list = _key
        for d in seq:
            if isinstance(key, str):
                if (key in d) and (d[key] == value) if not unpack else (d[key] in value):
                    if not multiple:
                        return d
                    matching.append(d)
            else:
                if (self.get_nested_key(d, key) == value) if not unpack else (self.get_nested_key(d, key) in value):
                    if not multiple:
                        return d
                    matching.append(d)
        return matching

    def get_remaining_keys(self, dict_: dict, keys: Iterable[str]) -> list[str]:
        return [k for k in dict_.keys() if k not in keys]

    def regex_get(self, dict_: dict, pattern: Union[re.Pattern, str], default: Any = None) -> Any:
        compare: Callable = ((lambda k_: bool(pattern.match(k))) if isinstance(pattern, re.Pattern)
                             else lambda k_: pattern in k_)
        for k, v in dict_.items():
            if compare(k):
                return v
        return default

    def populate_generic_numbered_resource(self,
                                           resource: dict,
                                           fmt_str: Optional[str] = None,
                                           **values: int) -> Union[dict[str, str], str]:
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

    def gen_separator_line(self, length: Any) -> str:
        """
        Generate a separator line with the provided length or the __len__ of the object passed

        :param length: The length of the separator line
        :return: The separator line
        """

        return '⎯' * (length if isinstance(length, int) else len(length))

    def option_display_list_format(self, options: Union[dict[str, str], list[str]]) -> str:
        """
        Utility method to construct a string representation of a numbered list from :class:`dict` or :class:`list`

        :param options: The options to build the list from
        :return: The created list string
        """

        if isinstance(options, dict):
            return '\n'.join([f"{self.e[self.itow(i+1)]}** {kv[0].capitalize()}** {kv[1]}"  # noqa
                              for i, kv in enumerate(options.items())])
        return '\n'.join([f"{self.e[self.itow(i+1)]} - {v}" for i, v in enumerate(options)])  # noqa

    def get_missing_keys_for_locale(self, locale: str) -> Optional[tuple[list[str], DictProxy, bool]]:
        """
        Get keys missing from a locale in comparison to the master locale

        :param locale: Any meta attribute of the locale
        :return: The missing keys for the locale and the confidence of the attribute match
        """

        locale_data: Optional[tuple[DictProxy, bool]] = self.get_locale_meta_by_attribute(locale)
        if locale_data:
            missing: list = list(
                set(item for item in self._missing_locale_keys[locale_data[0]['name']] if item is not None))
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
            for k, v in locale.items():
                match_: int = fuzz.token_set_ratio(attribute, v)
                if v == attribute or match_ > 80:
                    return locale, match_ == 100

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
                        self.log(f'missing key "{" -> ".join(path) if path else k}" patched.',
                                 f'locale-{Fore.LIGHTYELLOW_EX}{dict_.meta.name}')
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

        if group := match_.group('emoji_name'):
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
                        node[k] = r.LOCALE_EMOJI.sub(self._replace_emoji, v)

        for locale in self.l:
            _preprocess(locale)

    def fmt(self, ctx: commands.Context) -> object:
        """
        Instantiate a new Formatter object. Meant for binding to Context.

        :param ctx: The command invocation Context
        :return: The Formatter object created with the Context
        """

        self_: Manager = self

        class _Formatter:
            def __init__(self, ctx_: commands.Context):
                self.ctx: commands.Context = ctx_
                self.prefix: str = ''

            def __call__(self, resource: Union[tuple, str, list], /, *args, **kwargs) -> str:
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
                    self_.debug(f'Prefix mode is append, stripping op sign in \'{prefix}\'')
                    prefix: str = prefix[1:]
                    absolute: bool = False
                self.prefix: str = prefix.strip() + ' ' if absolute else self.prefix + prefix.strip() + ' '
                self_.debug(f'Locale formatting prefix set to \'{self.prefix.strip()}\' in '
                            f'\'{self_.get_last_call_from_callstack(frames_back=2)}\'')

        return _Formatter(ctx)
