import os
from typing import Union, Any


class DirProxy:
    def __init__(self, path: str, ext: Union[str, list, tuple]):
        for file in os.listdir(dir_ := os.path.join(os.getcwd(), path)):
            if file.endswith(ext):
                with open(os.path.join(dir_, file), "r") as fp:
                    setattr(self, file[: file.rindex(".")], fp.read())

    # Dumb, but it's just to stop PyCharm from bullying me
    def __getattr__(self, item: Any) -> Any:
        return getattr(self, item)
