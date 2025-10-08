"""
Structured JSON logging for BAEs experiment framework.

Provides consistent logging format across all modules with metadata support.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional


class JSONFormatter(logging.Formatter):
    """Format log records as JSON with structured metadata."""
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format a log record as JSON.
        
        Args:
            record: The log record to format
            
        Returns:
            JSON-formatted log string
        """
        log_entry: Dict[str, Any] = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'module': record.module,
            'message': record.getMessage()
        }
        
        # Add custom fields from record
        if hasattr(record, 'run_id'):
            log_entry['run_id'] = record.run_id
        if hasattr(record, 'framework'):
            log_entry['framework'] = record.framework
        if hasattr(record, 'step'):
            log_entry['step'] = record.step
        if hasattr(record, 'event'):
            log_entry['event'] = record.event
        if hasattr(record, 'metadata'):
            log_entry['metadata'] = record.metadata
            
        return json.dumps(log_entry)


def get_logger(name: str, log_file: Optional[str] = None) -> logging.Logger:
    """
    Get a configured logger instance with JSON formatting.
    
    Args:
        name: Logger name (typically __name__)
        log_file: Optional file path for log output
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.DEBUG)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(JSONFormatter())
    logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(JSONFormatter())
        logger.addHandler(file_handler)
    
    return logger


def log_event(
    logger: logging.Logger,
    level: str,
    message: str,
    run_id: Optional[str] = None,
    framework: Optional[str] = None,
    step: Optional[int] = None,
    event: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log an event with structured metadata.
    
    Args:
        logger: Logger instance
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        message: Log message
        run_id: Run identifier
        framework: Framework name
        step: Step number
        event: Event type
        metadata: Additional metadata dictionary
    """
    extra = {}
    if run_id:
        extra['run_id'] = run_id
    if framework:
        extra['framework'] = framework
    if step is not None:
        extra['step'] = step
    if event:
        extra['event'] = event
    if metadata:
        extra['metadata'] = metadata
    
    log_func = getattr(logger, level.lower())
    log_func(message, extra=extra)
