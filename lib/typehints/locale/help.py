from typing import TypedDict


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
