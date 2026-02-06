"""Tests for logging and error buffer."""

import pytest
from freefood.logging import log_error, get_errors, clear_errors, MAX_BUFFER_SIZE

def test_error_buffer_capture():
    """log_error should store errors in the buffer."""
    clear_errors()
    log_error("Test message", Exception("Test exception"))
    
    errors = get_errors()
    assert len(errors) == 1
    assert errors[0]["message"] == "Test message"
    assert "Test exception" in errors[0]["exception"]
    assert "timestamp" in errors[0]

def test_error_buffer_no_exception():
    """log_error should handle calls without exceptions."""
    clear_errors()
    log_error("Just a message")
    
    errors = get_errors()
    assert len(errors) == 1
    assert errors[0]["message"] == "Just a message"
    assert errors[0]["exception"] is None

def test_clear_errors():
    """clear_errors should empty the buffer."""
    log_error("Msg")
    assert len(get_errors()) > 0
    
    clear_errors()
    assert len(get_errors()) == 0

def test_error_buffer_pruning():
    """Buffer should not exceed MAX_BUFFER_SIZE."""
    clear_errors()
    for i in range(MAX_BUFFER_SIZE + 10):
        log_error(f"Message {i}")
    
    errors = get_errors()
    assert len(errors) == MAX_BUFFER_SIZE
    # Should contain the LATEST errors
    assert errors[-1]["message"] == f"Message {MAX_BUFFER_SIZE + 9}"
    assert errors[0]["message"] == "Message 10"
