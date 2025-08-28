import logging
from pathlib import Path
from typing import Optional
from config import Config
from datetime import datetime

_global_logger: Optional[logging.Logger] = None


def setup_logger(config: Config = None) -> logging.Logger:
    global _global_logger
    
    if _global_logger is not None:
        return _global_logger

    if config is not None:
        log_level = config.get("logging.level", "INFO")
        log_path = config.get("logging.log_path", "Logs")
        log_filename = f"tenderguru_parser_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    else:
        log_level = "INFO"
        log_path = "Logs"
        log_filename = f"tenderguru_parser_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

    logger = logging.getLogger("tenderguru_parser")
    
    level = getattr(logging, log_level.upper(), logging.INFO)
    logger.setLevel(level)

    logger.handlers.clear()

    formatter: logging.Formatter = logging.Formatter("%(asctime)s %(levelname)s (%(filename)s:%(lineno)d): %(message)s")

    ch: logging.Handler = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    Path(log_path).mkdir(parents=True, exist_ok=True)
    handler = logging.FileHandler(f"{log_path}/{log_filename}", encoding="utf-8")    
    handler.setFormatter(formatter)    

    logger.addHandler(handler)

    logger.info("Unified logger is ready")

    _global_logger = logger
    return logger


def get_logger() -> logging.Logger:
    global _global_logger
    if _global_logger is None:
        _global_logger = setup_logger()
    
    return _global_logger
