from typing import TypedDict


class CommandHelp(TypedDict, total=False):
    brief: str
    usage: str
    example: str
    description: str
