import json
import logging
import os
import sys


_RESET = "\x1b[0m"
_LEVEL_COLORS = {
    "DEBUG": "\x1b[36m",      # cyan
    "INFO": "\x1b[32m",       # green
    "WARNING": "\x1b[33m",    # yellow
    "ERROR": "\x1b[31m",      # red
    "CRITICAL": "\x1b[1;31m", # bold red
}


class ContextFormatter(logging.Formatter):
    """Append structured context from ``extra`` fields to log messages.

    When ``use_color`` is true and the active handler points at a TTY,
    the level name is wrapped in ANSI color codes for at-a-glance
    severity in a terminal. JSON context is always emitted plain so it
    remains greppable.
    """

    RESERVED_ATTRS = {
        "args",
        "asctime",
        "created",
        "exc_info",
        "exc_text",
        "filename",
        "funcName",
        "levelname",
        "levelno",
        "lineno",
        "module",
        "msecs",
        "message",
        "msg",
        "name",
        "pathname",
        "process",
        "processName",
        "relativeCreated",
        "stack_info",
        "thread",
        "threadName",
        "taskName",
    }

    def __init__(self, fmt: str, *, use_color: bool = True) -> None:
        super().__init__(fmt)
        self.use_color = use_color

    def format(self, record: logging.LogRecord) -> str:
        message = super().format(record)
        if self.use_color:
            color = _LEVEL_COLORS.get(record.levelname)
            if color:
                message = f"{color}{message}{_RESET}"

        context = {
            key: value
            for key, value in record.__dict__.items()
            if key not in self.RESERVED_ATTRS and not key.startswith("_")
        }
        if not context:
            return message

        return f"{message} | context={json.dumps(context, default=str, ensure_ascii=False, sort_keys=True)}"


def configure_logging() -> logging.Logger:
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    # Color is on for TTYs unless explicitly disabled via LOG_COLOR=0.
    # This keeps file/pipe output clean and CI logs readable.
    use_color = sys.stdout.isatty() and os.getenv("LOG_COLOR", "1") != "0"

    handler = logging.StreamHandler()
    handler.setFormatter(
        ContextFormatter(
            "%(asctime)s %(levelname)s [%(name)s] %(message)s",
            use_color=use_color,
        )
    )

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(level)
    root_logger.addHandler(handler)

    service_logger = logging.getLogger("gemma_rag")
    service_logger.setLevel(level)
    service_logger.propagate = True
    return service_logger


def get_logger(name: str | None = None) -> logging.Logger:
    if name:
        return logging.getLogger(f"gemma_rag.{name}")
    return logging.getLogger("gemma_rag")


logger = configure_logging()