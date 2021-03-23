import os
import json
from .json_proxy import JSONProxy
from typing import Union, Any, Optional


class DirProxy:
    """A simple wrapper around directories, mapping filenames to their contents.
    Files are mapped with their extensions removed, so 'file.json' would be 'DirProxy.file'

    Parameters
    ----------
    path: :class:`str`
        A path leading to the directory from which to extract files.
    ext: :class:`Optional[:class:`Union[:class:`str`, :class:`tuple`]`]`
        The extensions to include when mapping, if None, everything will be included.
    """

    def __init__(self, path: str, ext: Optional[Union[str, tuple]] = None, exclude: Union[str, tuple] = ()):
        for file in (os.listdir(dir_ := os.path.join(os.getcwd(), path))):
            if file not in exclude and ext is None or file.endswith(ext):
                with open(os.path.join(dir_, file), 'r') as fp:
                    if file.endswith('.json'):
                        setattr(self, file[:file.rindex('.')], JSONProxy(json.load(fp)))
                    else:
                        setattr(self, file[:file.rindex('.')], fp.read())

    def __getattr__(self, item: Any) -> Any:  # Dumb, but it's just to stop PyCharm from bullying me
        return getattr(self, item)
