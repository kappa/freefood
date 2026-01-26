"""Search parsing and highlighting helpers."""

from __future__ import annotations

import re

from rich.markup import escape


def parse_search_terms(query: str) -> list[str]:
    """Parse search query into terms, keeping quoted phrases together."""
    terms: list[str] = []
    buffer: list[str] = []
    in_quotes = False

    for ch in query:
        if ch == '"':
            if in_quotes:
                term = "".join(buffer).strip()
                if term:
                    terms.append(term)
                buffer = []
                in_quotes = False
            else:
                term = "".join(buffer).strip()
                if term:
                    terms.append(term)
                buffer = []
                in_quotes = True
            continue

        if ch.isspace() and not in_quotes:
            term = "".join(buffer).strip()
            if term:
                terms.append(term)
            buffer = []
            continue

        buffer.append(ch)

    term = "".join(buffer).strip()
    if term:
        terms.append(term)

    return terms


def highlight_text(text: str, terms: list[str]) -> str:
    """Return text with matching terms highlighted using Rich markup."""
    clean_terms = [t for t in terms if t]
    if not clean_terms:
        return text

    pattern = re.compile(
        "|".join(re.escape(term) for term in sorted(clean_terms, key=len, reverse=True)),
        re.IGNORECASE,
    )

    parts: list[str] = []
    last_idx = 0
    for match in pattern.finditer(text):
        start, end = match.span()
        if start > last_idx:
            parts.append(escape(text[last_idx:start]))
        parts.append(f"[reverse]{escape(text[start:end])}[/reverse]")
        last_idx = end

    parts.append(escape(text[last_idx:]))
    return "".join(parts)
