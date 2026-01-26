"""Tests for search helpers."""

from freefood.search import highlight_text, parse_search_terms


def test_parse_search_terms_handles_quotes() -> None:
    """parse_search_terms should keep quoted phrases together."""
    query = 'foo "bar baz" qux'
    assert parse_search_terms(query) == ["foo", "bar baz", "qux"]


def test_parse_search_terms_ignores_empty_terms() -> None:
    """parse_search_terms should ignore empty quoted phrases."""
    query = '  foo  ""   "bar baz"  '
    assert parse_search_terms(query) == ["foo", "bar baz"]


def test_highlight_text_is_case_insensitive() -> None:
    """highlight_text should wrap matches regardless of case."""
    result = highlight_text("Hello World", ["world"])
    assert result == "Hello [reverse]World[/reverse]"


def test_highlight_text_no_terms_returns_original() -> None:
    """highlight_text should return original text when no terms provided."""
    text = "Nothing to see"
    assert highlight_text(text, []) == text
