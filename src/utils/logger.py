"""
Structured JSON logging for BAEs experiment framework.

Provides consistent logging format across all modules with metadata support.
Implements per-run, per-step logging with component separation.
"""

import json
import logging
import os
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


class LogContext:
    """
    Thread-local context for run-specific logging.
    
    Tracks current run_id, framework, step, and log directory.
    Automatically creates step directories and manages log file paths.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __init__(self):
        """Initialize empty log context."""
        self.run_id: Optional[str] = None
        self.framework: Optional[str] = None
        self.logs_dir: Optional[Path] = None
        self.current_step: Optional[int] = None
        
    @classmethod
    def get_instance(cls) -> 'LogContext':
        """Get singleton instance (thread-safe)."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance
    
    def set_run_context(
        self,
        run_id: str,
        framework: str,
        logs_dir: Path
    ) -> None:
        """
        Set run-level context.
        
        Args:
            run_id: Run identifier
            framework: Framework name
            logs_dir: Base logs directory (runs/<framework>/<run_id>/logs)
        """
        self.run_id = run_id
        self.framework = framework
        self.logs_dir = logs_dir
        self.current_step = None
        
        # Create logs directory
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
    def set_step_context(self, step_num: int) -> None:
        """
        Set current step for step-based logging.
        
        Creates step directory if it doesn't exist.
        
        Args:
            step_num: Step number (1-indexed)
        """
        self.current_step = step_num
        
        if self.logs_dir:
            step_dir = self.logs_dir / f"step_{step_num:03d}"
            step_dir.mkdir(parents=True, exist_ok=True)
    
    def clear_step_context(self) -> None:
        """Clear current step (for run-level logging)."""
        self.current_step = None
        
    def get_log_file(self, component: str) -> Optional[Path]:
        """
        Get log file path for a component.
        
        Args:
            component: Component name (orchestrator, adapter, metrics, validator, reconciliation)
            
        Returns:
            Path to log file, or None if no context set
        """
        if not self.logs_dir:
            return None
        
        # Reconciliation is run-level (not per-step)
        if component == "reconciliation":
            return self.logs_dir / "reconciliation.log"
        
        # Run-level logging (pre/post run)
        if self.current_step is None:
            return self.logs_dir / "run.log"
        
        # Step-level logging
        step_dir = self.logs_dir / f"step_{self.current_step:03d}"
        return step_dir / f"{component}.log"


class DynamicFileHandler(logging.Handler):
    """
    File handler that dynamically determines log file based on LogContext.
    
    Switches log files automatically when step context changes.
    """
    
    def __init__(self, component: str):
        """
        Initialize dynamic file handler.
        
        Args:
            component: Component name for log file routing
        """
        super().__init__()
        self.component = component
        self.current_file = None
        self.current_handler = None
        self.setFormatter(JSONFormatter())
    
    def emit(self, record: logging.LogRecord) -> None:
        """
        Emit a log record to the appropriate file.
        
        Args:
            record: Log record to emit
        """
        context = LogContext.get_instance()
        log_file = context.get_log_file(self.component)
        
        if not log_file:
            # No context set - skip file logging
            return
        
        # Check if we need to switch files
        if log_file != self.current_file:
            # Close current handler if exists
            if self.current_handler:
                self.current_handler.close()
            
            # Create new handler for new file
            log_file.parent.mkdir(parents=True, exist_ok=True)
            self.current_handler = logging.FileHandler(log_file)
            self.current_handler.setFormatter(self.formatter)
            self.current_file = log_file
        
        # Emit to current handler
        if self.current_handler:
            self.current_handler.emit(record)
    
    def close(self) -> None:
        """Close the current file handler."""
        if self.current_handler:
            self.current_handler.close()
        super().close()


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


def get_logger(name: str, component: str = "run") -> logging.Logger:
    """
    Get a configured logger instance with JSON formatting.
    
    Automatically uses LogContext to determine log file path.
    Creates per-step, per-component log files when context is set.
    
    By default, logs are written only to files to keep terminal output clean.
    Set environment variable BAES_CONSOLE_LOGS=1 to enable console output.
    
    Args:
        name: Logger name (typically __name__)
        component: Component name (orchestrator, adapter, metrics, validator, reconciliation, run)
        
    Returns:
        Configured logger instance
    """
    # Create unique logger name including component to avoid conflicts
    logger_name = f"{name}.{component}"
    logger = logging.getLogger(logger_name)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.DEBUG)
    
    # Console handler (only if explicitly enabled via environment variable)
    # By default, logs go only to files to keep terminal output clean
    if os.environ.get('BAES_CONSOLE_LOGS', '').lower() in ('1', 'true', 'yes'):
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(JSONFormatter())
        logger.addHandler(console_handler)
    
    # Dynamic file handler that switches files based on context
    file_handler = DynamicFileHandler(component)
    file_handler.setLevel(logging.DEBUG)
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
