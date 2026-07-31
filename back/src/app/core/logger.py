import json
import logging
import os


class ContextFormatter(logging.Formatter):
    """Append structured context from ``extra`` fields to log messages."""

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

    def format(self, record: logging.LogRecord) -> str:
        message = super().format(record)
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

    handler = logging.StreamHandler()
    handler.setFormatter(
        ContextFormatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")
    )

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(level)
    root_logger.addHandler(handler)

    service_logger = logging.getLogger("pdf_service")
    service_logger.setLevel(level)
    service_logger.propagate = True
    return service_logger


def get_logger(name: str | None = None) -> logging.Logger:
    if name:
        return logging.getLogger(f"pdf_service.{name}")
    return logging.getLogger("pdf_service")


logger = configure_logging()
