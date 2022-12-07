#
# SPDX-License-Identifier: MIT
#
# Copyright (c) 2021-2022 Carsten Igel.
#
# This file is part of pdm-bump
# (see https://github.com/carstencodes/pdm-bump).
#
# This file is published using the MIT license.
# Refer to LICENSE for more information
#
from logging import (
    CRITICAL,
    DEBUG,
    ERROR,
    INFO,
    NOTSET,
    WARN,
    WARNING,
    Filter,
    Handler,
    Logger,
    LogRecord,
    StreamHandler,
    getLogger,
)
from sys import stderr, stdout
from typing import Any, Dict, Final, Mapping, Optional, Tuple, cast

# MyPy does not recognize this during pull requests
from pdm.termui import UI, Verbosity  # type: ignore


def _get_has_rich():
    try:
        # Justification: Required to find module, not more
        import rich  # noqa: F401 pylint: disable=C0415,W0611
    except ImportError:
        return False
    else:
        return True


HAS_RICH: Final[bool] = _get_has_rich()

if HAS_RICH:
    from rich.console import Console
    from rich.default_styles import DEFAULT_STYLES
    from rich.logging import RichHandler
    from rich.theme import Style, StyleType, Theme


TRACE: Final[int] = 5


class TermUIHandler(Handler):
    def __init__(self, ui: UI, level: int = NOTSET) -> None:
        super().__init__(level)
        self.__ui = ui

    def emit(self, record: LogRecord) -> None:
        msg_format = "{text}"
        if record.levelno in (WARN, WARNING):
            msg_format = "[warning]{text}[/warning]"
        verbosity: Verbosity = Verbosity.NORMAL
        if record.levelno == DEBUG:
            verbosity = Verbosity.DETAIL
        if record.levelno == TRACE:
            verbosity = Verbosity.DEBUG

        text = msg_format.format(text=self.format(record))
        self.__ui.echo(
            text,
            record.levelno in (ERROR, CRITICAL),
            verbosity,
        )


# Justification: Only one method to override
class _ErrorWarningsFilter(Filter):  # pylint: disable=R0903
    def __init__(self, invert: Optional[bool] = False) -> None:
        self.__invert: bool = invert or False
        super().__init__()

    def filter(self, record: LogRecord) -> bool:
        warning_and_above: Tuple[int, ...] = (WARN, WARNING, ERROR, CRITICAL)
        return (
            record.levelno in warning_and_above
            if not self.__invert
            else record.levelno not in warning_and_above
        )


class TracingLogger(Logger):
    def trace(self, msg: str, *args: Any, **kwargs) -> None:
        self.log(TRACE, msg, *args, **kwargs)

    # Justification: Overriding inherited method
    def makeRecord(  # pylint: disable=R0913
        self,
        name: str,
        level: int,
        fn: str,
        lno: int,
        msg: Any,
        args: Any,
        exc_info: Any,
        func: Optional[str] = None,
        extra: Optional[Mapping[str, Any]] = None,
        sinfo: Optional[str] = None,
    ) -> LogRecord:
        record: LogRecord = super().makeRecord(
            name, level, fn, lno, msg, args, exc_info, func, extra, sinfo
        )
        if level == TRACE:
            record.levelname = "TRACE"

        return record


Logger.manager.setLoggerClass(TracingLogger)


def _get_rich_logger() -> TracingLogger:
    _logger: TracingLogger = cast(TracingLogger, getLogger("pdm-bump"))

    styles: Dict[str, StyleType] = {}
    styles.update(DEFAULT_STYLES)
    styles.update(
        {
            "logging.level.notset": Style(dim=True),
            "logging.level.trace": Style(dim=True, color="bright_black"),
            "logging.level.debug": Style(dim=True, color="white"),
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

    _logger.addHandler(std_out_handler)
    _logger.addHandler(std_err_handler)

    _logger.level = INFO

    return _logger


def _get_std_logger() -> TracingLogger:
    _logger: TracingLogger = cast(TracingLogger, getLogger("pdm-bump"))
    # mypy: No overload variant of "StreamHandler"
    #       matches argument type "Handler"
    std_out: Handler = StreamHandler(stream=stdout)  # type: ignore
    std_err: Handler = StreamHandler(stream=stderr)  # type: ignore

    std_out.addFilter(_ErrorWarningsFilter(True))
    std_err.addFilter(_ErrorWarningsFilter(False))

    _logger.addHandler(std_out)
    _logger.addHandler(std_err)

    _logger.level = INFO

    return _logger


# Justification: Intended to use as a regular variable
logger: Final[TracingLogger] = (  # pylint: disable=C0103
    _get_std_logger() if not HAS_RICH else _get_rich_logger()
)


def update_logger_from_project_ui(ui_instance: UI) -> None:
    for handler in list(logger.handlers):
        logger.removeHandler(handler)

    new_handler: Handler = TermUIHandler(ui_instance)
    logger.addHandler(new_handler)


def traced_function(fun):
    def tracing_function(*args, **kwargs):
        try:
            logger.trace(
                "%s: Entering function", fun.__qualname__ or fun.__name__
            )
            return fun(*args, **kwargs)
        finally:
            logger.trace(
                "%s: Exiting function", fun.__qualname__ or fun.__name__
            )

    return tracing_function
