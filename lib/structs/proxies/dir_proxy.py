import os
import json
from .dict_proxy import DictProxy
from typing import Any, Optional


class DirProxy:
    """A simple wrapper around directories, mapping filenames to their contents.
    Files are mapped with their extensions removed, so 'file.json' would be 'DirProxy.file'

    Parameters
    ----------
    path: :class:`str`
        A path leading to the directory from which to extract files.
    ext: :class:`Optional[:class:`:class:`str` | :class:`tuple`]`
        The extensions to include when mapping, if None, everything will be included.
    """

    def __init__(self, path: str, ext: Optional[str | tuple] = None, exclude: str | tuple = ()):
        self.__items: list = []
        for file in (os.listdir(dir_ := os.path.join(os.getcwd(), path))):
            if file not in exclude and (ext is None or file.endswith(ext)):
                with open(os.path.join(dir_, file), 'r') as fp:
                    content: DictProxy | str = DictProxy(json.load(fp)) if file.endswith('.json') else fp.read()
                    self.__items.append(content)
                    setattr(self, file[:file.index('.')], content)

    def __iter__(self):
        yield from self.__items

    def __getitem__(self, item: Any) -> Any:
        return self.__items[item]
