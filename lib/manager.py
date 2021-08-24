import re
import os
import ast
import json
import dotenv
import discord
import zipfile
import os.path
import hashlib
import aiohttp
import operator
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
from motor.motor_asyncio import AsyncIOMotorClient
from lib.utils.decorators import normalize_identity
from typing import Optional, Union, Callable, Any, Reversible, Iterable, Iterator
from lib.typehints import DictSequence, AnyDict, Identity, GitBotGuild, AutomaticConversion
from lib.structs import DirProxy, DictProxy, GitCommandData, UserCollection, TypedCache, SelfHashingCache, CacheSchema


class Manager:
    """
    A class containing database, locale and utility functions

    :param github: The GitHubAPI instance to use
    :type github: :class:`lib.net.github.api.GitHubAPI`
    """

    def __init__(self, github):
        self.git = github
        self.env: DictProxy = DictProxy({k: v for k, v in dict(os.environ).items()
                                         if not self._set_env_directive(k, v)})
        self._env_directives: DictProxy = DictProxy()
        self._prepare_env()
        self.ses: aiohttp.ClientSession = self.git.ses
        self.db: AsyncIOMotorClient = getattr(AsyncIOMotorClient(self.env.db_connection),
                                              'store' if self.env.production else 'test')
        self.e: DictProxy = self.load_json('emoji')
        self.l: DirProxy = self.readdir('data/locale/', '.json', exclude='index.json')
        self.c: DictProxy = self.load_json('colors', lambda k, v: v if not (isinstance(v, str)
                                                                            and v.startswith('#')) else int(v[1:], 16))
        self.locale: DictProxy = self.load_json('locale/index')
        self.licenses: DictProxy = self.load_json('licenses')
        self.carbon_attachment_cache: SelfHashingCache = SelfHashingCache(max_age=60*60)
        self.autoconv_cache: TypedCache = TypedCache(CacheSchema(key=int, value=dict))
        self.locale_cache: TypedCache = TypedCache(CacheSchema(key=int, value=str), maxsize=256)
        self.loc_cache: TypedCache = TypedCache(CacheSchema(key=str, value=dict), maxsize=64, max_age=60*30)
        self.locale.master = getattr(self.l, str(self.locale.master))
        self.db.users = UserCollection(self.db.users, self.git, self)
        self._missing_locale_keys: dict = {l_['name']: [] for l_ in self.locale['languages']}
        self.__fix_missing_locales()
        self.__preprocess_locale_emojis()

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
                    self._env_directives or (directive in self._env_directives and overwrite):
                self._env_directives[directive] = value
                self.log(f'Directive set: {directive}->{value}', f'core-{Fore.LIGHTYELLOW_EX}env')
                return True
        return False

    def _prepare_env(self) -> None:
        """
        Private function meant to be called at the time of instantiating this class,
        loads .env with defaults from data/env_defaults.json
        """

        with open('data/env_defaults.json', 'r') as fp:
            env_defaults: dict = json.loads(fp.read())
            for k, v in env_defaults.items():
                if not self._set_env_directive(k, v) and k not in self.env:
                    self.env[k] = v
        self.load_dotenv()

    def _handle_env_binding(self, binding: dotenv.parser.Binding) -> None:
        """
        Handle an environment key->value binding.

        :param binding: The binding to handle
        """

        if not self._set_env_directive(binding.key, binding.value):
            try:
                if self._env_directives.get('eval_literal'):
                    if isinstance((parsed := self._eval_bool_literal_safe(binding.value)), bool):
                        self.env[binding.key] = parsed
                    else:
                        self.env[binding.key] = (parsed := self.parse_literal(binding.value))
                    self.log(f'Loaded as \'{type(parsed).__name__}\': {binding.key}',
                             f'core-{Fore.LIGHTYELLOW_EX}env')
                else:
                    self.env[binding.key] = binding.value
                    self.log(f'Loaded as \'str\': {binding.key}', f'core-{Fore.LIGHTYELLOW_EX}env')
                return
            except (ValueError, SyntaxError):
                self.env[binding.key] = binding.value
                self.log(f'Loaded as \'str\': {binding.key}',
                         f'core-{Fore.LIGHTYELLOW_EX}env')

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
                parsed: Iterator[dotenv.parser.Binding] = dotenv.parser.parse_stream(fp)
                for binding in parsed:
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
                self.log(message=f'{hex(id(object_))}[{hex(id(_object))}]: {size} bytes | type: {type(_object).__name__}',
                         category=f'debug-{Fore.LIGHTYELLOW_EX}sizeof[{Fore.LIGHTRED_EX}s{Style.RESET_ALL}]')

            for type_, handler in all_handlers.items():
                if isinstance(_object, type_):
                    size += sum(map(_sizeof, handler(_object)))
                    break
            return size

        final_size: int = _sizeof(object_)
        if verbose:
            self.log(message=f'{hex(id(object_))}: {final_size} bytes | type: {type(object_).__name__}',
                     category=f'debug-{Fore.LIGHTYELLOW_EX}sizeof[{Fore.LIGHTGREEN_EX}f{Style.RESET_ALL}]')

    def opt(self, obj: object, op: Callable, /, *args, **kwargs) -> Any:
        """
        Run an operation on an object if bool(object) == True

        :param obj: The object to run the operation on
        :param op: The operation to run if object is True
        :param args: Optional arguments for op
        :param kwargs: Optional keyword arguments for op
        :return: The result of the operation or the unchanged object
        """

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
            return match_.group('content').rstrip('\n')

    async def unzip_file(self, zip_path: str, output_dir: str) -> None:
        """
        Unzip a ZIP file to a specified location

        :param zip_path: The location of the ZIP file
        :param output_dir: The output directory to extract ZIP file contents to
        """

        if not os.path.exists(output_dir):
            os.mkdir(output_dir)
        with zipfile.ZipFile(zip_path, 'r') as _zip:
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
                return i
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

        to_load = './data/' + str(name).lower() + '.json' if name[-5:] != '.json' else ''
        with open(to_load, 'r') as fp:
            data: Union[dict, list] = json.load(fp)
        proxy: DictProxy = DictProxy(data)

        if apply_func:
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
                                                                    (r.REPO_RE, 'repo info'),
                                                                    (r.USER_ORG_RE, ('user info', 'org info')))
        for pattern, command_name in combos:
            if match := pattern.search(ctx.message.content):
                if isinstance(command_name, str):
                    command: commands.Command = ctx.bot.get_command(command_name)
                    kwargs: dict = dict(zip(dict(command.clean_params).keys(), match.groups()))
                else:
                    command: tuple[commands.Command, ...] = tuple(ctx.bot.get_command(name) for name in command_name)
                    kwargs: tuple[dict, ...] = tuple(dict(zip(dict(cmd.clean_params).keys(),
                                                              match.groups())) for cmd in command)
                return GitCommandData(command, kwargs)

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
        matched = [i for i in items if i['number'] == number]
        if matched:
            return matched[0]

    async def reverse(self, seq: Optional[Reversible]) -> Optional[Iterable]:
        """
        Reverse function with a None failsafe and recasting to the original type

        :param seq: The sequence to reverse
        :return: The reversed sequence if not None, else None
        """

        if seq:
            return type(seq)(reversed(seq))  # noqa

    def readdir(self, path: str, ext: Optional[Union[str, list, tuple]] = None, **kwargs) -> Optional[DirProxy]:
        """
        Read a directory and return a file-mapping object

        :param path: The directory path
        :param ext: The extensions to include, None for all
        :return: The mapped directory
        """

        if os.path.isdir(path):
            return DirProxy(path=path, ext=ext, **kwargs)

    async def enrich_context(self, ctx: commands.Context) -> commands.Context:
        """
        Bind useful attributes to the passed context object

        :param ctx: The context object to bind additional attributes to
        :return: The context object (With new attributes bound)
        """

        ctx.__nocache__ = False
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

        locale: str = self.locale.master.meta.name
        if cached := self.locale_cache.get(_id, None):
            locale: str = cached
        else:
            stored: Optional[str] = await self.db.users.getitem(_id, 'locale')
            if stored:
                locale: str = stored
                self.locale_cache[_id] = locale
        try:
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
                                 value: Any) -> Optional[AnyDict]:
        """
        Get a dictionary from an iterable, where d[key] == value

        :param seq: The sequence of dicts
        :param key: The key to check
        :param value: The wanted value
        :return: The dictionary with the matching value, if any
        """

        if len((_key := key.split())) > 1:
            key: list = _key
        for d in seq:
            if isinstance(key, str):
                if key in d and d[key] == value:
                    return d
            else:
                if self.get_nested_key(d, key) == value:
                    return d

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
                resource: str = self.prefix + resource if not resource.startswith(self.prefix) else resource
                try:
                    return self_.get_nested_key(self.ctx.l, resource).format(*args, **kwargs)
                except IndexError:
                    return self_.get_nested_key(self_.locale.master, resource).format(*args)

            def set_prefix(self, prefix: str) -> None:
                self.prefix: str = prefix.strip() + ' '

        return _Formatter(ctx)
