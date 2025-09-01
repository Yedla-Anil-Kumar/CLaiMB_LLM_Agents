# dev_env_scanner_agent/logging_utils.py
from __future__ import annotations
import time
from contextlib import contextmanager
from typing import Optional
from loguru import logger

def setup_logger(log_path: Optional[str] = "logs/bi_tracker.log", level: str = "INFO", serialize: bool = False) -> None:
    """
    Configure global loguru logging.
    - Console sink: human-readable
    - File sink: rotating file (optionally JSON serialized)
    """
    logger.remove()
    logger.add(
        sink=lambda msg: print(msg, end=""),
        level=level,
        colorize=True,
        backtrace=False,
        diagnose=False,
    )
    if log_path:
        logger.add(
            log_path,
            level=level,
            rotation="10 MB",   # rotate when file reaches 10 MB
            retention=10,       #  keep last 10 rotated files
            compression="zip",  # compress old logs
            serialize=serialize,
        )
@contextmanager
def timed(section: str):
    """Context manager for timing a code block, logging duration in ms."""
    start = time.perf_counter()
    try:
        logger.info(f"▶️ start: {section}")
        yield
    finally:
        dur_ms = (time.perf_counter() - start) * 1000.0
        logger.info(f"✅ done: {section} ({dur_ms:.2f} ms)")