import inspect
from discord.ext import commands
from typing import Callable, Union, Any


def restricted() -> commands.Command:
    """
    Allow only wulf to use commands with this decorator
    """

    def pred(ctx: commands.Context) -> bool:
        return ctx.author.id == 548803750634979340

    return commands.check(pred)


def normalize_identity(func: Callable) -> Callable:
    """
    Normalize the _id argument to be an instance of :class:`int`
    (instead of potential :class:`str` or :class:`discord.ext.commands.Context`

    :param func: The function to wrap with this decorator
    :return: The function with the _id argument normalized
    """

    def wrapper(*args: tuple, **kwargs: dict) -> Any:
        def normalize(_id: Union[int, str, commands.Context]) -> int:
            return int(_id) if not isinstance(_id, commands.Context) else _id.author.id

        if '_id' in kwargs:
            _id: Union[int, str, commands.Context] = kwargs['_id']
            kwargs['_id']: int = normalize(_id)
        else:
            spec: inspect.FullArgSpec = inspect.getfullargspec(func)
            if '_id' in spec.args:
                args: list = list(args)
                index: int = spec.args.index('_id')
                args[index] = normalize(args[index])
        return func(*args, **kwargs)
    return wrapper
