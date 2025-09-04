# from __future__ import annotations
# import time
# from contextlib import contextmanager
# from typing import Optional
# from loguru import logger

# def setup_logger(log_path: Optional[str] = "logs/cloud_infra.log", level: str = "INFO", serialize: bool = False) -> None:
#     """
#     Configure global loguru logging.
#     - Console sink: human-readable
#     - File sink: rotating file (optionally JSON serialized)
#     """
#     logger.remove()
#     logger.add(
#         sink=lambda msg: print(msg, end=""),
#         level=level,
#         colorize=True,
#         enqueue=True,
#         backtrace=False,
#         diagnose=False,
#     )
#     logger.add(
#         log_path,
#         rotation="10 MB",
#         retention="7 days",
#         level=level,
#         enqueue=True,
#         backtrace=False,
#         diagnose=False,
#         compression="zip",
#         serialize=serialize,
#     )

# @contextmanager
# def timed(section: str):
#     """Context manager for timing a code block, logging duration in ms."""
#     start = time.perf_counter()
#     try:
#         logger.info(f"▶️ start: {section}")
#         yield
#     finally:
#         dur_ms = (time.perf_counter() - start) * 1000.0
#         logger.info(f"✅ done: {section} ({dur_ms:.2f} ms)")

# cloud_infra_agent/logging_utils.py (or wherever you keep it)
from __future__ import annotations
import time
from contextlib import contextmanager
from typing import Optional
from loguru import logger

def setup_logger(log_path: Optional[str] = "logs/cloud_infra.log", level: str = "INFO", serialize: bool = False) -> None:
    """
    Configure global loguru logging.
    - Console sink: human-readable
    - File sink: rotating file (optionally JSON serialized)
    """
    logger.remove()

    log_format = "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {message}"

    # Console
    logger.add(
        sink=lambda msg: print(msg, end=""),
        level=level,
        colorize=True,
        enqueue=True,
        backtrace=False,
        diagnose=False,
        format=log_format,
    )
    # File
    logger.add(
        log_path,
        rotation="10 MB",
        retention="7 days",
        level=level,
        enqueue=True,
        backtrace=False,
        diagnose=False,
        compression="zip",
        serialize=serialize,
        format=log_format,
    )

# @contextmanager
# def timed(section: str):
#     """Context manager for timing a code block, logging duration in ms."""
#     start = time.perf_counter()
#     try:
#         logger.info(f"▶️ start: {section}")
#         yield
#     finally:
#         dur_ms = (time.perf_counter() - start) * 1000.0
#         logger.info(f"✅ done: {section} ({dur_ms:.2f} ms)")
@contextmanager
def timed(section: str, level: str = "INFO"):
    start = time.perf_counter()
    try:
        (logger.debug if level == "DEBUG" else logger.info)(f"▶️ start: {section}")
        yield
    finally:
        dur_ms = (time.perf_counter() - start) * 1000.0
        (logger.debug if level == "DEBUG" else logger.info)(f"✅ done:  {section} ({dur_ms:.2f} ms)")