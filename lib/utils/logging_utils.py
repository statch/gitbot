import logging
import colorama

fmt: str = '[{asctime}] - [{name}:{levelname}] - {message}'
extended_fmt: str = '[{asctime}] - [{name}:{levelname}] - [{filename}:#{lineno}:{funcName}()] - {message}'

FORMATS: dict[int, str] = {
    logging.DEBUG: extended_fmt,
    logging.INFO: fmt,
    logging.WARNING: fmt,
    logging.ERROR: extended_fmt,
    logging.CRITICAL: extended_fmt
}

FORMATS_COLOR: dict[int, str] = {
    logging.DEBUG: colorama.Fore.LIGHTBLACK_EX + extended_fmt + colorama.Style.RESET_ALL,
    logging.INFO: colorama.Fore.WHITE + fmt + colorama.Style.RESET_ALL,
    logging.WARNING: colorama.Fore.YELLOW + fmt + colorama.Style.RESET_ALL,
    logging.ERROR: colorama.Fore.LIGHTRED_EX + extended_fmt + colorama.Style.RESET_ALL,
    logging.CRITICAL: colorama.Fore.RED + extended_fmt + colorama.Style.RESET_ALL
}


class ColorfulLoggingFormatter(logging.Formatter):
    def format(self, record):
        log_fmt: str = FORMATS_COLOR.get(record.levelno)
        formatter: logging.Formatter = logging.Formatter(log_fmt, datefmt='%Y/%m/%d %H:%M:%S', style='{')
        return formatter.format(record)


class GitBotLoggingStreamHandler(logging.StreamHandler):
    def __init__(self, stream=None):
        super().__init__(stream)
        self.setFormatter(ColorfulLoggingFormatter())
