import logging
import sys
from pathlib import Path


def setup_logger(log_path: Path) -> logging.Logger:
    logger = logging.getLogger("diary_sync")
    logger.setLevel(logging.DEBUG)

    if logger.handlers:
        return logger  # already configured (e.g. during tests)

    formatter = logging.Formatter("[%(asctime)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formatter)
    logger.addHandler(console)

    file_handler = logging.FileHandler(log_path)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger
