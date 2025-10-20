"""
Unit tests for the per-run, per-step logging system.
"""

import json
import tempfile
from pathlib import Path
from src.utils.logger import LogContext, get_logger


class TestLogContext:
    """Tests for LogContext singleton."""
    
    def test_singleton_pattern(self):
        """Test that LogContext is a singleton."""
        context1 = LogContext.get_instance()
        context2 = LogContext.get_instance()
        assert context1 is context2
    
    def test_set_run_context(self):
        """Test setting run context creates logs directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logs_dir = Path(tmpdir) / "logs"
            context = LogContext.get_instance()
            
            context.set_run_context(
                run_id="test-run-123",
                framework="baes",
                logs_dir=logs_dir
            )
            
            assert context.run_id == "test-run-123"
            assert context.framework == "baes"
            assert context.logs_dir == logs_dir
            assert logs_dir.exists()
    
    def test_set_step_context(self):
        """Test setting step context creates step directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logs_dir = Path(tmpdir) / "logs"
            context = LogContext.get_instance()
            
            context.set_run_context(
                run_id="test-run-123",
                framework="baes",
                logs_dir=logs_dir
            )
            
            context.set_step_context(1)
            
            assert context.current_step == 1
            step_dir = logs_dir / "step_001"
            assert step_dir.exists()
    
    def test_clear_step_context(self):
        """Test clearing step context."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logs_dir = Path(tmpdir) / "logs"
            context = LogContext.get_instance()
            
            context.set_run_context(
                run_id="test-run-123",
                framework="baes",
                logs_dir=logs_dir
            )
            
            context.set_step_context(1)
            assert context.current_step == 1
            
            context.clear_step_context()
            assert context.current_step is None
    
    def test_get_log_file_run_level(self):
        """Test getting run-level log file path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logs_dir = Path(tmpdir) / "logs"
            context = LogContext.get_instance()
            
            context.set_run_context(
                run_id="test-run-123",
                framework="baes",
                logs_dir=logs_dir
            )
            
            # No step set - should return run.log
            log_file = context.get_log_file("orchestrator")
            assert log_file == logs_dir / "run.log"
    
    def test_get_log_file_step_level(self):
        """Test getting step-level log file path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logs_dir = Path(tmpdir) / "logs"
            context = LogContext.get_instance()
            
            context.set_run_context(
                run_id="test-run-123",
                framework="baes",
                logs_dir=logs_dir
            )
            
            context.set_step_context(2)
            
            log_file = context.get_log_file("adapter")
            assert log_file == logs_dir / "step_002" / "adapter.log"
    
    def test_get_log_file_reconciliation(self):
        """Test that reconciliation always uses run-level log."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logs_dir = Path(tmpdir) / "logs"
            context = LogContext.get_instance()
            
            context.set_run_context(
                run_id="test-run-123",
                framework="baes",
                logs_dir=logs_dir
            )
            
            # Even with step set, reconciliation should be run-level
            context.set_step_context(1)
            log_file = context.get_log_file("reconciliation")
            assert log_file == logs_dir / "reconciliation.log"
    
    def test_get_log_file_without_context(self):
        """Test that get_log_file returns None without context."""
        context = LogContext.get_instance()
        context.logs_dir = None
        
        log_file = context.get_log_file("adapter")
        assert log_file is None


class TestComponentLoggers:
    """Tests for component-specific loggers."""
    
    def test_logger_with_context_writes_to_file(self):
        """Test that logger writes to correct file when context is set."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logs_dir = Path(tmpdir) / "logs"
            context = LogContext.get_instance()
            
            context.set_run_context(
                run_id="test-run-123",
                framework="baes",
                logs_dir=logs_dir
            )
            
            context.set_step_context(1)
            
            # Create logger and log message
            logger = get_logger(__name__, component="adapter")
            logger.info("Test message", extra={'run_id': 'test-run-123', 'step': 1})
            
            # Verify file exists and contains message
            log_file = logs_dir / "step_001" / "adapter.log"
            assert log_file.exists()
            
            content = log_file.read_text()
            assert "Test message" in content
            
            # Verify JSON structure
            log_entry = json.loads(content.strip())
            assert log_entry['message'] == "Test message"
            assert log_entry['level'] == "INFO"
            assert log_entry['run_id'] == "test-run-123"
            assert log_entry['step'] == 1
    
    def test_different_components_different_files(self):
        """Test that different components write to different files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logs_dir = Path(tmpdir) / "logs"
            context = LogContext.get_instance()
            
            context.set_run_context(
                run_id="test-run-123",
                framework="baes",
                logs_dir=logs_dir
            )
            
            context.set_step_context(1)
            
            # Create multiple loggers
            adapter_logger = get_logger("test.adapter", component="adapter")
            metrics_logger = get_logger("test.metrics", component="metrics")
            
            adapter_logger.info("Adapter message")
            metrics_logger.info("Metrics message")
            
            # Verify separate files
            adapter_log = logs_dir / "step_001" / "adapter.log"
            metrics_log = logs_dir / "step_001" / "metrics.log"
            
            assert adapter_log.exists()
            assert metrics_log.exists()
            
            assert "Adapter message" in adapter_log.read_text()
            assert "Metrics message" in metrics_log.read_text()
            assert "Metrics message" not in adapter_log.read_text()
    
    def test_step_transition(self):
        """Test that logger correctly switches files when step changes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logs_dir = Path(tmpdir) / "logs"
            context = LogContext.get_instance()
            
            context.set_run_context(
                run_id="test-run-123",
                framework="baes",
                logs_dir=logs_dir
            )
            
            # Step 1
            context.set_step_context(1)
            logger = get_logger("test.step", component="orchestrator")
            logger.info("Step 1 message")
            
            # Step 2
            context.set_step_context(2)
            logger.info("Step 2 message")
            
            # Verify messages in correct files
            step1_log = logs_dir / "step_001" / "orchestrator.log"
            step2_log = logs_dir / "step_002" / "orchestrator.log"
            
            assert step1_log.exists()
            assert step2_log.exists()
            
            assert "Step 1 message" in step1_log.read_text()
            assert "Step 2 message" in step2_log.read_text()
            assert "Step 2 message" not in step1_log.read_text()


class TestLoggerFallback:
    """Tests for logger fallback behavior without context."""
    
    def test_logger_without_context_works(self):
        """Test that logger works (console-only) without context set."""
        context = LogContext.get_instance()
        context.logs_dir = None
        context.current_step = None
        
        # Should not raise exception
        logger = get_logger(__name__, component="adapter")
        logger.info("Test message without context")
        
        # Should work but not create any files
        # (logs go to console only)
