import logging
import os
from datetime import datetime

def get_logger(name: str) -> logging.Logger:
    """
    Creates a logger that writes to both console and log file.
    Each run creates a new timestamped log file.
    """
    # create logs directory
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../logs")
    os.makedirs(log_dir, exist_ok=True)

    # timestamped log file per run
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"crew_run_{timestamp}.log")

    # create logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # avoid duplicate handlers if called multiple times
    if logger.handlers:
        return logger

    # ── File Handler — captures everything ──
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_formatter)

    # ── Console Handler — shows INFO and above ──
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter("%(levelname)-8s | %(message)s")
    console_handler.setFormatter(console_formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logger.info(f"Logger initialized — writing to {log_file}")
    return logger