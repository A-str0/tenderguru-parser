import logging
from pathlib import Path
from typing import Optional
from config import Config
from datetime import datetime
import os
import glob

_global_logger: Optional[logging.Logger] = None


class RotatingFileHandlerWithCleanup(logging.FileHandler):
    def __init__(self, filename, max_files=10, max_file_size=10*1024*1024, **kwargs):
        self.max_files = max_files
        self.max_file_size = max_file_size
        self.cleanup_old_logs(filename)
        super().__init__(filename, **kwargs)
    
    def cleanup_old_logs(self, current_filename):
        log_dir = os.path.dirname(current_filename)
        if not log_dir:
            log_dir = "."
        
        log_files = glob.glob(os.path.join(log_dir, "tenderguru_parser_*.log"))
        log_files.sort(key=os.path.getmtime, reverse=True)
        
        if len(log_files) > self.max_files:
            for old_file in log_files[self.max_files:]:
                try:
                    os.remove(old_file)
                except OSError:
                    pass
    
    def emit(self, record):
        if self.stream is not None and self.stream.tell() + len(self.format(record)) > self.max_file_size:
            self.rotate()
        super().emit(record)
    
    def rotate(self):
        if self.stream:
            self.stream.close()
        
        base_path = self.baseFilename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        new_filename = f"{base_path.rsplit('.', 1)[0]}_{timestamp}.log"
        
        try:
            os.rename(self.baseFilename, new_filename)
        except OSError:
            pass
        
        self.cleanup_old_logs(self.baseFilename)
        
        self.stream = self._open()


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
    full_log_path = f"{log_path}/{log_filename}"
    
    handler = RotatingFileHandlerWithCleanup(
        full_log_path, 
        max_files=10,  # Keep last 10 log files
        max_file_size=5*1024*1024,  # 5MB max file size
        encoding="utf-8"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    logger.info("Unified logger is ready with rotation")

    _global_logger = logger
    return logger


def get_logger() -> logging.Logger:
    global _global_logger
    if _global_logger is None:
        _global_logger = setup_logger()
    
    return _global_logger
