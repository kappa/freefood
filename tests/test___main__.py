"""Tests for __main__ entry point."""

from unittest.mock import MagicMock, patch


def test_main_creates_app_and_runs():
    """main() creates a FreeFoodApp and calls run()."""
    mock_app = MagicMock()

    with patch("freefood.app.FreeFoodApp", return_value=mock_app):
        from importlib import reload

        import freefood.__main__ as mod

        reload(mod)
        mod.main()

    mock_app.run.assert_called_once()
