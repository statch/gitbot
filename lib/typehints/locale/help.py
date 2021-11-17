from typing import TypedDict
from lib.utils.decorators import GitBotCommand


class ArgumentExplainer(TypedDict):
    name: str
    content: str


class CommandHelp(TypedDict):
    brief: str
    usage: str
    example: str
    description: str
    argument_explainers: list[str]
    qa_resource: str
    required_permissions: list[str]


class CommandGroupHelp(TypedDict):
    brief: str
    usage: str
    example: str
    description: str
    argument_explainers: list[str]
    qa_resource: str
    required_permissions: list[str]
    commands: list[GitBotCommand | str]
