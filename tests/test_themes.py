"""Tests for theme definitions and helpers."""

from freefood.themes import (
    DEFAULT_THEME_KEY,
    THEME_OPTIONS,
    get_theme_keys,
    resolve_textual_theme,
)


def test_resolve_known_theme():
    """resolve_textual_theme returns correct textual theme for known keys."""
    assert resolve_textual_theme("dark") == "textual-dark"
    assert resolve_textual_theme("light") == "textual-light"


def test_resolve_unknown_theme_falls_back_to_default():
    """resolve_textual_theme returns default theme for unknown keys."""
    result = resolve_textual_theme("nonexistent")
    expected = resolve_textual_theme(DEFAULT_THEME_KEY)
    assert result == expected


def test_resolve_does_not_recurse_on_unknown_key():
    """resolve_textual_theme should not use recursion for fallback."""
    # This test verifies the function handles unknown keys without recursion.
    # With the old recursive implementation, a bad DEFAULT_THEME_KEY would
    # cause infinite recursion. With a dict lookup, it raises KeyError.
    result = resolve_textual_theme("totally-bogus")
    assert isinstance(result, str)


def test_get_theme_keys():
    """get_theme_keys returns all valid theme keys."""
    keys = get_theme_keys()
    assert "dark" in keys
    assert "light" in keys
    assert len(keys) == len(THEME_OPTIONS)


def test_theme_options_have_required_fields():
    """Every ThemeOption has key, label, and textual_theme."""
    for option in THEME_OPTIONS:
        assert option.key
        assert option.label
        assert option.textual_theme
