import logging
import os
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Path & Directory Configuration
# ---------------------------------------------------------------------------
# Anchors logs directory to the project root (Hotel-Reservation-Prediction/logs)
# regardless of where python is executed from (notebooks, tests, subfolders, etc.)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOGS_DIR = PROJECT_ROOT / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Daily log file naming convention
CURRENT_DATE = datetime.now().strftime("%Y-%m-%d")
LOG_FILE_PATH = LOGS_DIR / f"app_{CURRENT_DATE}.log"

# Default logging level from environment (defaults to INFO)
LOG_LEVEL_STR = os.getenv("LOG_LEVEL", "INFO").upper()
DEFAULT_LOG_LEVEL = getattr(logging, LOG_LEVEL_STR, logging.INFO)


# ---------------------------------------------------------------------------
# ANSI Color Formatter for Interactive Console Output
# ---------------------------------------------------------------------------
class ColoredFormatter(logging.Formatter):
    """
    Custom console formatter that adds ANSI color codes to log levels
    for high readability during development and debugging.
    """

    RESET = "\033[0m"
    BOLD = "\033[1m"
    COLORS = {
        logging.DEBUG: "\033[36m",     # Cyan
        logging.INFO: "\033[32m",      # Green
        logging.WARNING: "\033[33m",   # Yellow
        logging.ERROR: "\033[31m",     # Red
        logging.CRITICAL: "\033[1;31m" # Bold Red
    }

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelno, self.RESET)
        # Apply color code only to the level name
        levelname_colored = f"{color}{record.levelname:<8}{self.RESET}"
        
        # Format message safely
        original_levelname = record.levelname
        record.levelname = levelname_colored
        formatted_message = super().format(record)
        record.levelname = original_levelname
        return formatted_message


# ---------------------------------------------------------------------------
# Handler Factories
# ---------------------------------------------------------------------------
def _get_file_handler(log_file: Path) -> RotatingFileHandler:
    """
    Creates a rotating file handler with standard non-colored formatting.
    Rotates at 10 MB per file, keeping up to 5 backups.
    """
    file_format = logging.Formatter(
        fmt="[%(asctime)s] [%(process)d] %(levelname)-8s [%(name)s] [%(filename)s:%(lineno)d] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler = RotatingFileHandler(
        filename=str(log_file),
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setFormatter(file_format)
    file_handler.setLevel(DEFAULT_LOG_LEVEL)
    return file_handler


def _get_console_handler() -> logging.StreamHandler:
    """
    Creates a console/stream handler sending logs to stdout with colors
    if stdout is a terminal (TTY), or clean formatting in CI/CD environments.
    """
    console_format_str = "[%(asctime)s] %(levelname)-8s [%(name)s] (%(filename)s:%(lineno)d) - %(message)s"
    
    # Check if stdout is an interactive terminal to apply color formatting
    if sys.stdout.isatty():
        console_formatter = ColoredFormatter(
            fmt=console_format_str,
            datefmt="%H:%M:%S"
        )
    else:
        console_formatter = logging.Formatter(
            fmt=console_format_str,
            datefmt="%Y-%m-%d %H:%M:%S"
        )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(DEFAULT_LOG_LEVEL)
    return console_handler


# ---------------------------------------------------------------------------
# Public Logger Provider
# ---------------------------------------------------------------------------
def get_logger(name: Optional[str] = None, log_file: Optional[Path] = None) -> logging.Logger:
    """
    Returns a configured Logger instance with dual handlers (Console & Rotating File).
    Prevents duplicate handlers if called multiple times for the same module.

    Args:
        name: Name of the logger (typically `__name__`).
        log_file: Optional custom log file path. Defaults to `LOG_FILE_PATH`.

    Returns:
        logging.Logger: Configured logger ready for use.
    """
    logger_name = name or "app"
    logger = logging.getLogger(logger_name)
    logger.setLevel(DEFAULT_LOG_LEVEL)

    # Avoid adding duplicate handlers if logger was already initialized
    if not logger.handlers:
        target_log_file = log_file or LOG_FILE_PATH
        logger.addHandler(_get_file_handler(target_log_file))
        logger.addHandler(_get_console_handler())
        # Avoid propagating to the root logger to prevent duplicate terminal lines
        logger.propagate = False

    return logger


# Default application-wide logger instance for convenience
logger = get_logger("HotelReservation")


# ---------------------------------------------------------------------------
# Self-Test / Demo Verification
# ---------------------------------------------------------------------------
# if __name__ == "__main__":
#     test_logger = get_logger("TestModule")
    
#     test_logger.debug("This is a DEBUG message (diagnostic info).")
#     test_logger.info("This is an INFO message (general event).")
#     test_logger.warning("This is a WARNING message (potential issue).")
#     test_logger.error("This is an ERROR message (failure occurred).")
#     test_logger.critical("This is a CRITICAL message (system compromised).")

#     try:
#         1 / 0
#     except ZeroDivisionError:
#         test_logger.exception("An exception occurred with full traceback captured:")
    
#     print(f"\n[✓] Logs successfully recorded to: {LOG_FILE_PATH}")