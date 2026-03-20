"""
logging_config.py
-----------------
Configures application-wide logging. Logs are written to both a rotating
file (bot.log) and the console (WARNING level and above only), keeping
output clean during normal operation.
"""

import logging
import logging.handlers
import os
from pathlib import Path


LOG_FILE = Path(__file__).parent.parent / "bot.log"
MAX_BYTES = 5 * 1024 * 1024   # 5 MB per file
BACKUP_COUNT = 3               # keep up to 3 rotated files


def setup_logging(log_level: str = "DEBUG") -> logging.Logger:
    """
    Initialise and return the root logger for the trading bot.

    File handler  → DEBUG (captures every API call / response)
    Console handler → WARNING (only surfaces issues to the terminal)

    Args:
        log_level: Minimum level for the file handler (default DEBUG).

    Returns:
        The configured 'tradingbot' logger instance.
    """
    logger = logging.getLogger("tradingbot")

    # Avoid adding duplicate handlers if called more than once
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # --- File handler (rotating) -------------------------------------------
    file_handler = logging.handlers.RotatingFileHandler(
        filename=LOG_FILE,
        maxBytes=MAX_BYTES,
        backupCount=BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setLevel(getattr(logging, log_level.upper(), logging.DEBUG))
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # --- Console handler (warnings and above only) --------------------------
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


# Module-level logger that all other modules import
logger = setup_logging()
