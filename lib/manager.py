import json
import re
import os
import functools
import operator
import discord
import zipfile
import os.path
from colorama import Style, Fore
from motor.motor_asyncio import AsyncIOMotorClient
from discord.ext import commands
from lib.typehints import DictSequence, AnyDict, Identity
from lib.structs import DirProxy, DictProxy, GitCommandData, UserCollection
from lib.utils import regex as r
from lib.utils.decorators import normalize_identity
from typing import Optional, Union, Callable, Any, Reversible, List, Iterable, Coroutine, Tuple
from fuzzywuzzy import fuzz


class Manager:
    """
    A class containing database, locale and utility functions

    Parameters
    ----------
    github: :class:`core.net.github.api.GitHubAPI`
        The GitHub API instance to use
    """

    def __init__(self, github):
        self.git = github
        self.db: AsyncIOMotorClient = AsyncIOMotorClient(os.getenv('DB_CONNECTION')).store
        self.e: DictProxy = self.load_json('emoji')
        self.l: DirProxy = DirProxy('data/locale/', '.json', exclude='index.json')
        self.locale: DictProxy = self.load_json('locale/index')
        self.licenses: DictProxy = self.load_json('licenses')
        self.patterns: tuple = ((r.GITHUB_LINES_RE, 'snippet'),
                                (r.GITLAB_LINES_RE, 'snippet'),
                                (r.ISSUE_RE, 'issue'),
                                (r.PR_RE, 'pr'),
                                (r.REPO_RE, 'repo'),
                                (r.USER_ORG_RE, 'user_org'))
        self.type_to_func: dict = {'repo': self.git.get_repo,
                                   'user_org': None,
                                   'issue': self.git.get_issue,
                                   'pr': self.git.get_pull_request,
                                   'snippet': 'snippet'}
        self.locale_cache: dict = {}
        setattr(self.locale, 'master', self.l.en)
        setattr(self.db, 'users', UserCollection(self.db.users, self.git, self))
        self._missing_locale_keys: dict = {l_['name']: [] for l_ in self.locale['languages']}
        self.__fix_missing_locales()

    def get_closest_match_from_iterable(self, to_match: str, iterable: Iterable[str]) -> str:
        """
        Iterate through an iterable of :class:`str` and return the item that resembles to_match the most.

        :param to_match: The :class:`str` to pair with a match
        :param iterable: The iterable to search for matches
        :return: The closest match
        """

        best = 0, None
        for i in iterable:
            if (m := fuzz.token_set_ratio(str(i), to_match)) > best[0]:
                best = m, str(i)
        return best[1]

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

        print(f'{bracket_color}[{category_color}{category}{bracket_color}]: {Style.RESET_ALL}{message_color}{message}')

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
                       value: Optional[Any] = None) -> Optional[Tuple[str, ...]]:
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

        def _recursive(__prev: tuple = ()) -> Optional[Tuple[str, ...]]:
            reduced: dict = self.get_nested_key(dict_, __prev)
            for k, v in reduced.items():
                if k == key and (value is None or (value is not None and v == value)):
                    return *__prev, key
                if isinstance(v, dict):
                    if ret := _recursive((*__prev, k)):
                        return ret
        return _recursive()

    def strip_codeblock(self, codeblock: str) -> str:
        """
        Extract code from the codeblock while retaining indentation.

        :param codeblock: The codeblock to strip
        :return: The code extracted from the codeblock
        """

        return re.sub(r'^.*?\n', '\n', codeblock.strip('`')).rstrip().lstrip('\n')

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

    def load_json(self, name: str) -> DictProxy:
        """
        Load a JSON file from the data dir

        :param name: The name of the JSON file
        :return: The loaded JSON wrapped in DictProxy
        """

        to_load = './data/' + str(name).lower() + '.json' if name[-5:] != '.json' else ''
        with open(to_load, 'r') as fp:
            data: Union[dict, list] = json.load(fp)
        return DictProxy(data)

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

    async def get_link_reference(self, link: str) -> Optional[Union[GitCommandData, str, tuple]]:
        """
        Get the command data required for invocation from a link

        :param link: The link to exchange for command data
        :return: The command data requested
        """

        for pattern in self.patterns:
            match: list = re.findall(pattern[0], link)
            if match:
                match: Union[str, tuple] = match[0]
                action: Optional[Union[Callable, str]] = self.type_to_func[pattern[1]]
                if isinstance(action, str):
                    return GitCommandData(link, 'snippet', link)
                if isinstance(match, tuple) and action:
                    match: tuple = tuple(i if not i.isnumeric() else int(i) for i in match)
                    obj: Union[dict, str] = await action(match[0], int(match[1]))
                    if isinstance(obj, str):
                        return obj, pattern[1]
                    return GitCommandData(obj, pattern[1], match)
                if not action:
                    if (obj := await self.git.get_user((m := match))) is None:
                        obj: Optional[dict] = await self.git.get_org(m)
                        return GitCommandData(obj, 'org', m) if obj is not None else 'no-user-or-org'
                    return GitCommandData(obj, 'user', m)
                repo = await action(match)
                return GitCommandData(repo, pattern[1], match) if repo is not None else 'repo'

    async def get_most_common(self, items: Union[list, tuple]) -> Any:
        """
        Get the most common item from a list/tuple

        :param items: The iterable to return the most common item of
        :return: The most common item from the iterable
        """

        return max(set(items), key=items.count)

    async def validate_number(self, number: str, items: List[AnyDict]) -> Optional[dict]:
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
            return type(seq)(reversed(seq))

    async def readdir(self, path: str, ext: Optional[Union[str, list, tuple]] = None) -> DirProxy:
        """
        Read a directory and return a file-mapping object

        :param path: The directory path
        :param ext: The extensions to include, None for all
        :return: The mapped directory
        """

        if os.path.isdir(path):
            return DirProxy(path=path, ext=ext)

    async def error(self, ctx: commands.Context, msg: str, **kwargs) -> None:
        """
        Context.send() with an emoji slapped in front ;-;

        :param ctx: The command invocation context
        :param msg: The message content
        :param kwargs: ctx.send keyword arguments
        """

        await ctx.send(f'{self.e.err}  {msg}', **kwargs)

    def error_ctx_bindable(self, ctx: commands.Context) -> functools.partial[Coroutine]:
        """
        Manager.error with the Context parameter removed

        :param ctx: The command invocation context
        :return: A partial version of Manager.error bindable to Context
        """

        return functools.partial(self.error, ctx)

    @normalize_identity
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

    def get_nested_key(self, dict_: AnyDict, key_: Union[Iterable[str], str]) -> Any:
        """
        Get a nested dictionary key

        :param dict_: The dictionary to get the key from
        :param key_: The key to get
        :return: The value associated with the key
        """

        return functools.reduce(operator.getitem, key_ if not isinstance(key_, str) else key_.split(), dict_)

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

    def get_missing_keys_for_locale(self, locale: str) -> Optional[Tuple[List[str], bool]]:
        """
        Get keys missing from a locale in comparison to the master locale

        :param locale: Any meta attribute of the locale
        :return: The missing keys for the locale and the confidence of the attribute match
        """

        locale_data: Optional[Tuple[DictProxy, bool]] = self.get_locale_meta_by_attribute(locale)
        if locale_data:
            return list(set(item for item in self._missing_locale_keys[locale_data[0]['name']] if item is not None)), locale_data[1]

    def get_locale_meta_by_attribute(self, attribute: str) -> Optional[Tuple[DictProxy, bool]]:
        """
        Get a locale from a potentially malformed attribute.
        If there isn't a match above 80, returns None

        :param attribute: The attribute to match
        :return: The locale or None if not matched
        """

        for locale in self.locale.languages:
            for k, v in locale.items():
                match: int = fuzz.token_set_ratio(attribute, v)
                if v == attribute or match > 80:
                    return locale, match == 100

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
                        self.log(f'missing key "{k}" patched.', f'locale-{Fore.LIGHTYELLOW_EX}{dict_.meta.name}')
                        self._missing_locale_keys[dict_.meta.name].append(self.dict_full_path(ref_.actual, k, v))
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

            def __call__(self, resource: Union[tuple, str, list], /, *args) -> str:
                resource: str = self.prefix + resource if not resource.startswith(self.prefix) else resource
                try:
                    return self_.get_nested_key(self.ctx.l, resource).format(*args)
                except IndexError:
                    return self_.get_nested_key(self_.locale.master, resource).format(*args)

            def set_prefix(self, prefix: str) -> None:
                self.prefix: str = prefix.strip() + ' '

        return _Formatter(ctx)
