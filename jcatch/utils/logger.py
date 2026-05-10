"""Unified logger for jcatch project."""

import logging
import sys

# 日志格式
LOG_FORMAT = "[%(levelname)s] %(asctime)s %(name)s - %(message)s"
DATE_FORMAT = "%H:%M:%S"

# 步骤前缀符号
STEP_PREFIX = "⟳"  # 进行中/主要步骤
SUCCESS_PREFIX = "✓"  # 成功
ERROR_PREFIX = "✗"     # 错误

# 缩进符号（3个空格）
INDENT = "   "


def get_logger(name: str) -> logging.Logger:
    """Get or create a logger, ensuring it's from jcatch package."""
    logger_name = f"jcatch.{name}"
    logger = logging.getLogger(logger_name)
    return logger


def setup_logger(name: str = "jcatch", level: int = logging.INFO) -> logging.Logger:
    """Setup and return a configured logger.

    Args:
        name: Logger name, typically __name__
        level: Logging level (default: INFO)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    return logger


def log_step(step_num: int, total_steps: int, message: str) -> None:
    """Log a main step.

    Args:
        step_num: Current step number (1-based)
        total_steps: Total number of steps
        message: Step description
    """
    logger = get_logger(__name__)
    logger.info(f"{step_num}/{total_steps} {message}")


def log_sub_step(message: str) -> None:
    """Log a sub-step with indent.

    Args:
        message: Sub-step description
    """
    logger = get_logger(__name__)
    logger.info(f"{STEP_PREFIX}{INDENT}{message}")


def log_success(message: str) -> None:
    """Log a success message.

    Args:
        message: Success description
    """
    logger = get_logger(__name__)
    logger.info(f"{SUCCESS_PREFIX}{INDENT}{message}")


def log_error(message: str) -> None:
    """Log an error message.

    Args:
        message: Error description
    """
    logger = get_logger(__name__)
    logger.error(f"{ERROR_PREFIX}{INDENT}{message}")


def setup_root_logger():
    """Setup root logger with console handler."""
    logger = logging.getLogger("jcatch")
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.INFO)
        handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
        logger.addHandler(handler)


# 导入时自动配置 root logger
setup_root_logger()
