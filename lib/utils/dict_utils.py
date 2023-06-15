from typing import Any, Iterable
from lib.typehints import DictSequence, AnyDict


__all__: tuple[str, ...] = (
    'get_by_key_from_sequence',
    'dict_full_path',
    'get_nested_key',
    'get_all_dict_paths',
    'set_nested_key'
)


def get_by_key_from_sequence(seq: DictSequence,
                             key: str,
                             value: Any,
                             multiple: bool = False,
                             unpack: bool = False) -> AnyDict | list[AnyDict] | None:
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
        if ((isinstance(key, str) and (key in d) and (d[key] == value) if not unpack else (d[key] in value)) or
            get_nested_key(d, key) == value) if not unpack else (get_nested_key(d, key) in value):
            if not multiple:
                return d
            matching.append(d)
    return matching

def dict_full_path(dict_: AnyDict,
                   key: str,
                   value: Any = None) -> tuple[str, ...] | None:
    """
    Get the full path of a dictionary key in the form of a tuple.
    The value is an optional parameter that can be used to determine which key's path to return if many are present.

    :param dict_: The dictionary to which the key belongs
    :param key: The key to get the full path to
    :param value: The optional value for determining if a key is the right one
    :return: None if key not in dict_ or dict_[key] != value if value is not None else the full path to the key
    """

    def _recursive(__prev: tuple = ()) -> tuple[str, ...] | None:
        reduced: dict = get_nested_key(dict_, __prev)
        for k, v in reduced.items():
            if k == key and (value is None or (value is not None and v == value)):
                return *__prev, key
            if isinstance(v, dict):
                if ret := _recursive((*__prev, k)):
                    return ret

    return _recursive()


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
        if k.endswith(']'):
            index_start = k.index('[')
            index = int(k[index_start + 1:-1])
            dict_ = dict_[index]
        else:
            dict_ = dict_.get(k)

    return dict_

def get_all_dict_paths(d: dict, __path: tuple[str, ...] | None = None) -> list[tuple[str, ...]]:
    """
    Get all paths in a dictionary

    :param d: The dictionary to get the paths from
    :return: A list of paths
    """
    __path: tuple = () if __path is None else __path
    paths: list = []
    for k, v in d.items():
        if isinstance(v, dict):
            paths.extend(get_all_dict_paths(v, __path + (k,)))
        else:
            paths.append(__path + (k,))
    return paths

def set_nested_key(dict_: AnyDict, key: Iterable[str] | str, value: Any, sep: str = ' ') -> None:
    """
    Set a nested dictionary key

    :param dict_: The dictionary to set the key in
    :param key: The key to set
    :param value: The value to set
    :param sep: The separator to use if key is a string
    """
    if isinstance(key, str):
        key = key.split(sep=sep)

    for k in key[:-1]:
        if k.endswith(']'):
            index_start = k.index('[')
            index = int(k[index_start + 1:-1])
            dict_ = dict_[index]
        else:
            dict_ = dict_.setdefault(k, {})

    dict_[key[-1]] = value
