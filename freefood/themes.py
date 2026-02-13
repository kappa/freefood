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
    for option in THEME_OPTIONS:
        if option.key == theme_key:
            return option.textual_theme

    return resolve_textual_theme(DEFAULT_THEME_KEY)
