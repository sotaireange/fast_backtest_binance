# loggers.py
import logging
from rich.logging import RichHandler
from rich.console import Console
from pathlib import Path
import os

LOG_DIR = "logs"
TIME_FORMAT = "[%X %d-%m-%Y]"
FORMAT_CONSOLE_LOG = "%(message)s"
FORMAT_FILE_LOG = "%(asctime)s %(levelname)s %(name)s [%(module)s.%(funcName)s(%(lineno)d)] | %(message)s"
LOG_LEVEL = logging.INFO

console = Console()

def ensure_log_dir():
    Path(LOG_DIR).mkdir(parents=True, exist_ok=True)

def get_file_handler(name: str, level: int = LOG_LEVEL) -> logging.Handler:
    ensure_log_dir()
    filepath = os.path.join(LOG_DIR, f"{name}.log")
    handler = logging.FileHandler(filepath, encoding="utf-8")
    formatter = logging.Formatter(FORMAT_FILE_LOG, datefmt=TIME_FORMAT)
    handler.setFormatter(formatter)
    handler.setLevel(level)
    return handler

def get_logger(name: str, log_to_console: bool = True, log_both: bool = False) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.handlers.clear()
    logger.setLevel(LOG_LEVEL)
    logger.propagate = False

    if log_to_console:
        console_handler = RichHandler(console=console, show_time=False, show_path=False, markup=True)
        console_handler.setLevel(LOG_LEVEL)
        console_handler.setFormatter(logging.Formatter(FORMAT_CONSOLE_LOG))
        logger.addHandler(console_handler)
        if log_both:
            logger.addHandler(get_file_handler(name))
    else:
        logger.addHandler(get_file_handler(name))

    return logger

def redirect_external_loggers_to_file(file_name="all_logs"):
    ensure_log_dir()
    file_handler = get_file_handler(file_name)
    for name, logger in logging.root.manager.loggerDict.items():
        if isinstance(logger, logging.Logger):
            if getattr(logger, "already_redirected", False):
                continue
            logger.handlers.clear()
            logger.addHandler(file_handler)
            logger.propagate = False
            logger.already_redirected = True
