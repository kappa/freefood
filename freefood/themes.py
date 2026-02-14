"""Theme definitions and helpers."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ThemeOption:
    """A selectable app theme option."""

    key: str
    label: str
    textual_theme: str


THEME_OPTIONS: tuple[ThemeOption, ...] = (
    ThemeOption(key="dark", label="Dark", textual_theme="textual-dark"),
    ThemeOption(key="light", label="Light", textual_theme="textual-light"),
)

DEFAULT_THEME_KEY = "dark"


def get_theme_keys() -> set[str]:
    """Get all valid theme keys."""
    return {theme.key for theme in THEME_OPTIONS}


def resolve_textual_theme(theme_key: str) -> str:
    """Resolve a theme key to a Textual theme name."""
    theme_map = {option.key: option.textual_theme for option in THEME_OPTIONS}
    return theme_map.get(theme_key, theme_map[DEFAULT_THEME_KEY])
