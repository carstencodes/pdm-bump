from logging import (CRITICAL, ERROR, WARN, WARNING, Filter, Handler, Logger,
                     LogRecord, StreamHandler, getLogger)
from sys import stderr, stdout
from typing import Dict, Final, Optional, Tuple

try:
    import rich
except ImportError:
    HAS_RICH: Final[bool] = False
else:
    HAS_RICH: Final[bool] = True

if HAS_RICH:
    from rich.console import Console
    from rich.default_styles import DEFAULT_STYLES
    from rich.logging import RichHandler
    from rich.theme import Style, StyleType, Theme


class _ErrorWarningsFilter(Filter):
    def __init__(self, invert: Optional[bool] = False) -> None:
        self.__invert: bool = invert or False

    def filter(self, record: LogRecord) -> bool:
        warning_and_above: Tuple[int] = (WARN, WARNING, ERROR, CRITICAL)
        return (
            record.levelno in warning_and_above
            if not self.__invert
            else record.levelno not in warning_and_above
        )


def _get_rich_logger() -> Logger:
    logger: Logger = getLogger("pdm-bump")

    styles: Dict[str, StyleType] = dict()
    styles.update(DEFAULT_STYLES)
    styles.update(
        {
            "logging.level.notset": Style(dim=True),
            "logging.level.debug": Style(dim=True, color="bright_black"),
            "logging.level.info": Style(color="blue"),
            "logging.level.warning": Style(color="yellow"),
            "logging.level.error": Style(color="bright_red"),
            "logging.level.critical": Style(color="red"),
        }
    )
    logging_theme: Theme = Theme(styles)

    std_out: Console = Console(stderr=False, theme=logging_theme)
    std_err: Console = Console(stderr=True, theme=logging_theme)

    std_out_handler: Handler = RichHandler(console=std_out)
    std_err_handler: Handler = RichHandler(console=std_err)

    std_out_handler.addFilter(_ErrorWarningsFilter(True))
    std_err_handler.addFilter(_ErrorWarningsFilter(False))

    logger.addHandler(std_out_handler)
    logger.addHandler(std_err_handler)

    return logger


def _get_std_logger() -> Logger:
    logger: Logger = getLogger("pdm-bump")
    std_out: Handler = StreamHandler(stream=std_out)
    std_err: Handler = StreamHandler(stream=std_err)

    std_out.addFilter(_ErrorWarningsFilter(True))
    std_err.addFilter(_ErrorWarningsFilter(False))

    logger.addHandler(std_out)
    logger.addHandler(std_err)
    return logger


logger: Logger = _get_std_logger() if not HAS_RICH else _get_rich_logger()


def traced_function(f):
    def tracing_function(*args, **kwargs):
        try:
            logger.debug("%s: Entering function", f.__qualname__ or f.__name__)
            return f(*args, **kwargs)
        finally:
            logger.debug("%s: Exiting function", f.__qualname__ or f.__name__)

    return tracing_function
