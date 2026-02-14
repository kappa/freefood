# Test Suite Speed Analysis

**Date:** 2026-02-13
**Status:** Not started (lower priority)

## Current State

- **622 tests** in **~120 seconds** (~0.19s average per test)
- All tests pass, coverage at 96.39%

## Slowest Tests (--durations=30)

| Time | Test | Category |
|---|---|---|
| 5.47s | `test_feed_screen.py::TestAutoSelectionOnScroll::test_selection_moves_when_focused_post_scrolls_out_of_view` | Scroll simulation with timers |
| 1.33s | `test_post_screen.py::TestPostScreenMenuNavigation::test_selecting_errors_navigates` | ErrorsScreen mount overhead |
| 1.28s | `test_theme_screen.py::TestThemeScreenMenuNavigation::test_selecting_errors_view_navigates` | ErrorsScreen mount overhead |
| 1.10s | `test_search_screen.py::TestSearchMenuNavigation::test_selecting_errors_navigates` | ErrorsScreen mount overhead |
| 1.09s | `test_notifications_screen.py::TestNotificationsMenuNavigation::test_selecting_errors_navigates` | ErrorsScreen mount overhead |
| 0.84s | `test_post_widget.py::TestPostBlockOnKeyEdgeCases::test_on_key_escape_in_comment_edit_mode` | Widget interaction |
| 0.82s | `test_post_widget.py::TestPostBlockCommentEditing::test_comment_cancel_edit_restores_view` | Widget interaction |
| 0.75s | `test_feed_screen.py::TestCommentLikeUnlike::test_comment_like_keeps_focus_on_same_button` | Widget interaction |
| 0.75s | `test_edit.py::TestEditPostMode::test_cancel_exits_edit_mode` | Widget interaction |
| 0.74s | `test_comment_compose.py::TestCommentComposeIntegration::test_submit_hides_compose_and_adds_comment` | Widget interaction |
| 0.60-0.73s | ~20 more tests | Widget editing, compose, post mode tests |

## Distribution

- **1 test** > 5s (auto-scroll outlier)
- **4 tests** at 1.0-1.3s (all ErrorsScreen navigation)
- **~25 tests** at 0.6-0.84s (widget interaction tests)
- **~592 tests** < 0.6s

## Root Cause

The bottleneck is **Textual's `run_test()` pilot pattern**. Every async test:
1. Creates a full App instance
2. Mounts all widgets (CSS parsing, layout)
3. Runs the async event loop
4. Tears down

This overhead adds up across 622 tests. There's no single catastrophic test (except the scroll simulation).

## Potential Approaches

1. **Reduce `run_test()` usage** — For tests that only verify message passing or state changes, test at the unit level without mounting the full UI. E.g., call handler methods directly on screen instances without the pilot.

2. **Share app fixtures** — Group tests that need the same screen setup and reuse a single mounted app across multiple tests in a class (pytest class-scoped fixtures).

3. **Speed up ErrorsScreen mount** — The 4 navigation tests that push ErrorsScreen are all >1s. ErrorsScreen's compose reads the error log and creates widgets. Could be lazy-loaded or simplified in test context.

4. **Fix the scroll test outlier** — 5.47s for one test is excessive. It likely uses `set_timer` with real delays. Could use smaller delays or mock timers.

5. **Parallel test execution** — Use `pytest-xdist` to run tests across multiple processes. Would require making tests independent (no shared global state like the error log).
