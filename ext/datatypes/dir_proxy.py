import os
import json
from .json_proxy import JSONProxy
from typing import Union, Any


class DirProxy:
    def __init__(self, path: str, ext: Union[str, list, tuple]):
        for file in (os.listdir(dir_ := os.path.join(os.getcwd(), path))):
            if file.endswith(ext):
                with open(os.path.join(dir_, file), 'r') as fp:
                    if file.endswith('.json'):
                        setattr(self, file[:file.rindex('.')], JSONProxy(json.load(fp)))
                    else:
                        setattr(self, file[:file.rindex('.')], fp.read())

    def __getattr__(self, item: Any) -> Any:  # Dumb, but it's just to stop PyCharm from bullying me
        return getattr(self, item)
