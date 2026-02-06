"""Tests for ErrorsScreen."""

import pytest
from textual.app import App
from freefood.logging import log_error, clear_errors
from freefood.screens.errors import ErrorsScreen
from freefood.state import AppState

class MockApp(App):
    def __init__(self):
        super().__init__()
        self.state = AppState()

@pytest.mark.asyncio
async def test_errors_screen_displays_errors():
    """ErrorsScreen should render logged errors."""
    clear_errors()
    log_error("UI Test Error", Exception("UI Exception"))
    
    app = MockApp()
    async with app.run_test() as pilot:
        await app.push_screen(ErrorsScreen())
        
        # Check if error message is rendered
        assert pilot.app.screen.query(".error-message")
        assert pilot.app.screen.query(".error-exception")
        
        # Verify specific content
        static_msg = pilot.app.screen.query_one(".error-message")
        assert "UI Test Error" in str(static_msg.render())

@pytest.mark.asyncio
async def test_errors_screen_clear_action():
    """Pressing 'c' should clear errors."""
    clear_errors()
    log_error("Error to clear")
    
    app = MockApp()
    async with app.run_test() as pilot:
        await app.push_screen(ErrorsScreen())
        assert pilot.app.screen.query(".error-entry")
        
        # Press 'c' to clear
        await pilot.press("c")
        
        # Should now show empty state
        assert not pilot.app.screen.query(".error-entry")
        assert pilot.app.screen.query_one("#errors-empty")
