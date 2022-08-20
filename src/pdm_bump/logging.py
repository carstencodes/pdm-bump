from typing import Final, Optional, Tuple, Dict
from logging import Logger, Handler, StreamHandler, Filter, getLogger, LogRecord
from logging import WARN, WARNING, ERROR, CRITICAL
from sys import stderr, stdout

try:
    import rich
except ImportError:
    HAS_RICH: Final[bool] = False
else:
    HAS_RICH: Final[bool] = True

if HAS_RICH:
    from rich.console import Console
    from rich.theme import Theme, StyleType, Style
    from rich.default_styles import DEFAULT_STYLES
    from rich.logging import RichHandler


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

    logger.addFilter(std_out_handler)
    logger.addFilter(std_err_handler)

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
