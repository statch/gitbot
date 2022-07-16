from typing import TypedDict, Literal

__all__: tuple = ('AutomaticConversionSettings',)


class AutomaticConversionSettings(TypedDict):
    codeblock: bool
    gh_url: bool
    gh_lines: Literal[0, 1, 2]
