# FreeFood Project Instructions

## Critical: Always Use Superpowers

**ALWAYS use Superpowers skills.** This is not optional.

- **Bugs/test failures:** Use `superpowers:systematic-debugging` BEFORE attempting any fix
- **New features/bug fixes:** Use `superpowers:test-driven-development` - write failing test first
- **Multiple independent tasks:** Use `superpowers:subagent-driven-development` to run in parallel
- **Planning:** Use `superpowers:writing-plans` for multi-step tasks

## Running Tests

This is a venv project. Use the venv Python/pytest:

```bash
# Run all tests
/home/kappa/work/frf/freefood/.venv/bin/pytest tests/ -v

# Run specific test class
/home/kappa/work/frf/freefood/.venv/bin/pytest tests/test_post_widget.py::TestPostModeNavigation -v

# Run single test
/home/kappa/work/frf/freefood/.venv/bin/pytest tests/test_post_widget.py::TestPostModeNavigation::test_tab_stays_within_post -v
```

## Quality Gate

Before committing, all checks must pass with zero errors:

```bash
# Lint and format
/home/kappa/work/frf/freefood/.venv/bin/ruff check freefood/ tests/
/home/kappa/work/frf/freefood/.venv/bin/ruff format --check freefood/ tests/

# Type check
/home/kappa/work/frf/freefood/.venv/bin/mypy freefood/

# Tests with coverage (must not drop below threshold in pyproject.toml)
/home/kappa/work/frf/freefood/.venv/bin/pytest tests/
```

New code must include tests. Coverage must not regress.

## Running the App

```bash
/home/kappa/work/frf/freefood/.venv/bin/freefood
```

## TDD Workflow (Strict)

1. **RED:** Write a failing test first
2. **Verify RED:** Run test, confirm it fails for the right reason
3. **GREEN:** Write minimal code to pass the test
4. **Verify GREEN:** Run test, confirm it passes
5. **REFACTOR:** Clean up if needed, keeping tests green

Never write production code without a failing test first.

## Testing Practices

**Assert behavior, not implementation.** Tests should verify *what* the code achieves (state changes, visible output, user-facing behavior), not *how* it achieves it (which internal method was called, what intermediary data structures look like). Tests that assert on outcomes survive refactors; tests that assert on mechanics break when implementation changes even if behavior is identical.

- Good: `assert state.current_view == View.HOME` (observable outcome)
- Bad: `assert any(isinstance(s, FeedScreen) for s in app.pushed_screens)` (implementation detail)

## Project Structure

- `freefood/` - Main package
  - `widgets/` - Textual widgets (PostBlock, CommentBlock, MenuBar)
  - `screens/` - Textual screens (FeedScreen)
  - `models.py` - Data models (Post, Comment, User, View)
  - `state.py` - Application state management
  - `api.py` - FreeFeed API client
- `tests/` - Test files

## FreeFeed API Documentation

The unofficial API reference is at `../frfc/docs/freefeed-api.md`. When discovering new API behavior or errors in the doc, update it there (it's shared across projects).

## Debugging the FreeFeed API

Write small debug scripts to explore actual API responses. The API sometimes returns different structures than expected (e.g., `posts` is a dict for single-post endpoints but a list for timelines).

```python
#!/usr/bin/env python3
import asyncio
import configparser
import httpx

async def main():
    config = configparser.ConfigParser()
    config.read("/home/kappa/.config/freefood/config.ini")
    token = config.get("auth", "token")

    async with httpx.AsyncClient(
        base_url="https://freefeed.net",
        headers={"Authorization": f"Bearer {token}"},
    ) as client:
        response = await client.get("/v2/timelines/home", params={"limit": 1})
        data = response.json()
        print(f"Keys: {list(data.keys())}")
        print(f"posts type: {type(data.get('posts'))}")

asyncio.run(main())
```

Run with: `/home/kappa/work/frf/freefood/.venv/bin/python script.py`
