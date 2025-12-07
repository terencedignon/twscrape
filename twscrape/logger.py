import os
import sys
from typing import Literal, cast, Optional

from loguru import logger

_TLOGLEVEL = Literal["TRACE", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


def _load_from_env() -> _TLOGLEVEL:
    env = os.getenv("TWS_LOG_LEVEL", "INFO").upper()
    if env not in ["TRACE", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
        logger.warning(f"Invalid log level '{env}' in TWS_LOG_LEVEL. Defaulting to INFO.")
        return "INFO"

    return cast(_TLOGLEVEL, env)


_LOG_LEVEL: _TLOGLEVEL = _load_from_env()
_FILE_HANDLER_ID: Optional[int] = None


def set_log_level(level: _TLOGLEVEL):
    global _LOG_LEVEL
    _LOG_LEVEL = level


def _filter(r):
    return r["level"].no >= logger.level(_LOG_LEVEL).no


def add_file_handler(
    file_path: str,
    level: Optional[_TLOGLEVEL] = None,
    format: str = "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
    rotation: Optional[str] = None,
    retention: Optional[str] = None,
    compression: Optional[str] = None
) -> int:
    """
    Add file logging handler to logger.

    Args:
        file_path: Path to log file
        level: Log level for file handler (defaults to global _LOG_LEVEL)
        format: Log format string (default: detailed format with timestamp, level, location, message)
        rotation: When to rotate log file (e.g., "500 MB", "1 day", "1 week")
        retention: How long to keep old logs (e.g., "10 days", "1 month")
        compression: Compression format (e.g., "zip", "gz")

    Returns:
        Handler ID for later removal

    Example:
        >>> from twscrape.logger import logger, add_file_handler
        >>> handler_id = add_file_handler("crawler.log", level="DEBUG", rotation="10 MB")
        >>> logger.info("This goes to both console and file")
    """
    global _FILE_HANDLER_ID

    # Use global level if not specified
    file_level = level or _LOG_LEVEL

    handler_id = logger.add(
        file_path,
        format=format,
        level=file_level,
        rotation=rotation,
        retention=retention,
        compression=compression,
        backtrace=True,
        diagnose=True
    )

    # Track the most recent file handler
    _FILE_HANDLER_ID = handler_id

    logger.info(f"📝 File logging enabled: {file_path} (level: {file_level})")

    return handler_id


def remove_file_handler(handler_id: Optional[int] = None):
    """
    Remove file logging handler.

    Args:
        handler_id: Specific handler ID to remove (defaults to most recent file handler)
    """
    global _FILE_HANDLER_ID

    if handler_id is None:
        handler_id = _FILE_HANDLER_ID

    if handler_id is not None:
        logger.remove(handler_id)
        logger.info(f"File logging handler removed: {handler_id}")
        _FILE_HANDLER_ID = None


logger.remove()
logger.add(sys.stderr, filter=_filter)
