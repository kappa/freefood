"""Entry point for freefood console client."""

from freefood.app import FreeFoodApp


def main() -> None:
    """Run the FreeFood application."""
    app = FreeFoodApp()
    app.run()


if __name__ == "__main__":
    main()
