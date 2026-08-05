"""Вспомогательные функции."""
import logging
import sys
from pathlib import Path


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """Настройка логгера."""
    logger = logging.getLogger("churn")
    logger.setLevel(level)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger


def ensure_dir(path: Path) -> None:
    """Создаёт директорию, если её нет."""
    path.mkdir(parents=True, exist_ok=True)
