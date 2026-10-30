import logging
import json
import traceback
from datetime import datetime
from typing import Any, Dict, Optional
from config.settings import settings

class StructuredLogger:
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            self.logger.addHandler(handler)
            
        self.logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))

    def _format_log(self, level: str, message: str, context: Optional[Dict[str, Any]] = None, exc_info: Optional[Exception] = None) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": level,
            "message": message,
            "logger": self.logger.name
        }
        
        if context:
            log_entry["context"] = context
            
        if exc_info:
            log_entry["exception"] = str(exc_info)
            log_entry["traceback"] = traceback.format_exc()
            
        if settings.enable_structured_logging:
            return json.dumps(log_entry)
        
        return f"[{log_entry['timestamp']}] {level} - {self.logger.name} - {message} {context or ''}"

    def info(self, message: str, context: Optional[Dict[str, Any]] = None):
        if self.logger.isEnabledFor(logging.INFO):
            self.logger.info(self._format_log("INFO", message, context))

    def error(self, message: str, context: Optional[Dict[str, Any]] = None, exc_info: Optional[Exception] = None):
        if self.logger.isEnabledFor(logging.ERROR):
            self.logger.error(self._format_log("ERROR", message, context, exc_info))

    def warning(self, message: str, context: Optional[Dict[str, Any]] = None):
        if self.logger.isEnabledFor(logging.WARNING):
            self.logger.warning(self._format_log("WARNING", message, context))

    def debug(self, message: str, context: Optional[Dict[str, Any]] = None):
        if self.logger.isEnabledFor(logging.DEBUG):
            self.logger.debug(self._format_log("DEBUG", message, context))

def get_logger(name: str) -> StructuredLogger:
    return StructuredLogger(name)
