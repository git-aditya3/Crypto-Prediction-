"""
Logger v5 MAX - Structured logging, thread-safe, rotation, metrics, versioning
"""
import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
import threading
from datetime import datetime

from ..config import get_config

config = get_config()
LOG_DIR = config.project_root / "logs"
LOG_DIR.mkdir(exist_ok=True)

_loggers = {}
_loggers_lock = threading.Lock()

class VersionFilter(logging.Filter):
    def filter(self, record):
        if not hasattr(record, 'version'):
            record.version = "v5_max"
        return True

def get_logger(name: str = "crypto_prediction", level: int = logging.INFO) -> logging.Logger:
    with _loggers_lock:
        if name in _loggers:
            return _loggers[name]

        logger = logging.getLogger(name)
        if logger.handlers:
            _loggers[name] = logger
            return logger

        logger.setLevel(level)
        
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | v5_max | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        # Console handler
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(level)
        ch.setFormatter(formatter)
        ch.addFilter(VersionFilter())
        logger.addHandler(ch)

        # File handler with rotation v5
        try:
            fh = RotatingFileHandler(
                LOG_DIR / f"{name}_v5.log",
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5,
                encoding='utf-8'
            )
            fh.setLevel(level)
            fh.setFormatter(formatter)
            fh.addFilter(VersionFilter())
            logger.addHandler(fh)
        except Exception:
            # Fallback to simple file handler
            try:
                fh = logging.FileHandler(LOG_DIR / f"{name}.log")
                fh.setLevel(level)
                fh.setFormatter(formatter)
                logger.addHandler(fh)
            except Exception:
                pass

        # Prevent propagation
        logger.propagate = False

        _loggers[name] = logger
        return logger

def get_logger_metrics() -> dict:
    with _loggers_lock:
        return {
            "loggers": len(_loggers),
            "log_dir": str(LOG_DIR),
            "version": "v5_max",
            "timestamp": datetime.utcnow().isoformat()
        }
