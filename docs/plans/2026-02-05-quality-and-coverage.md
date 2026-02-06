# Quality & Coverage Implementation Plan

**Goal:** Establish quality infrastructure — tooling, static analysis, coverage measurement, and CI enforcement — creating a safety net for future development.

**Principles:**
- This iteration is purely about quality infrastructure. No new features, no refactoring.
- Behavior-preserving refactoring is deferred to a follow-up iteration that benefits from this safety net.
- **ruff** for both linting and formatting (no black).
- **mypy** with gradual strictness (start at defaults, tighten incrementally).
- **pytest-cov** with a ratchet model (measure baseline, prevent regression).

## Phase 1: Tooling Setup

Add `ruff`, `mypy`, and `pytest-cov` to `[project.optional-dependencies] dev` in `pyproject.toml`.

**ruff configuration (`[tool.ruff]`):**
- Enable rule sets: `E`, `F`, `W` (core), `UP` (pyupgrade), `B` (bugbear), `I` (isort).
- Format settings: defaults (should match current code style).

**mypy configuration (`[tool.mypy]`):**
- `python_version = "3.11"`
- `warn_return_any = true`
- `warn_unused_configs = true`
- Start at default strictness. Strict flags will be enabled incrementally in later iterations.

**pytest-cov:**
- Run coverage measurement but don't set a `--cov-fail-under` threshold yet — that comes after measuring the baseline in Phase 4.

## Phase 2: Format & Lint

1. Run `ruff format .` and `ruff check --fix .` across the entire codebase.
2. Commit the result as a single commit with a clear message (e.g., "style: apply ruff formatting and lint fixes").
3. Create `.git-blame-ignore-revs` pointing at that commit so `git blame` stays clean.
4. Fix any remaining ruff issues that `--fix` couldn't auto-resolve.

## Phase 3: Type Checking

1. Run `mypy .` at default settings, fix all errors.
2. Expect the most work around Textual widget signatures and httpx types, where third-party stubs may be incomplete.
3. Once clean at defaults, consider enabling `disallow_untyped_defs` as the first strict flag — but only if the effort is manageable. Otherwise defer to the next iteration.

## Phase 4: Coverage Baseline

1. Run `pytest --cov=freefood --cov-report=term-missing` to measure current coverage.
2. Record the baseline number.
3. Set `--cov-fail-under` to that baseline (rounded down to nearest integer).
4. Add the coverage threshold to `[tool.pytest.ini_options]` in `pyproject.toml` so it's enforced locally too.

## Phase 5: CI Workflow

Create `.github/workflows/ci.yml`, triggered on push and PR to `main`. Separate from the existing `build.yml` (which handles release builds only).

Single job, single Python version (3.11):

1. **Lint:** `ruff check .` and `ruff format --check .`
2. **Types:** `mypy .`
3. **Test:** `pytest --cov=freefood --cov-fail-under=<baseline>`

## Phase 6: Update CLAUDE.md

Add quality gate instructions to the project's `CLAUDE.md` so all coding agents maintain the bar:

- Run `ruff check .` and `ruff format --check .` before committing — zero warnings required.
- Run `mypy .` before committing — zero errors required.
- New code must include tests. Coverage must not drop below the ratchet threshold.
- Include the exact commands to run.

---

## Follow-up: Refactoring (deferred to next iteration)

These are behavior-preserving refactors to be done *after* the quality safety net is in place, so regressions are caught automatically.

- **`freefood/api.py`:** Refactor repetitive `get_`/`post_`/`put_` methods into a unified `_request()` wrapper handling auth headers, error catching, and logging.
- **`freefood/api.py` — `_denormalize_posts`:** Break down the complex denormalization logic into smaller, individually testable functions. Add specific tests for missing references and type mismatches.
- **`freefood/widgets/post.py`:** Extract header rendering, body formatting, and action bars from the 928-line `PostBlock` class into smaller, testable helper methods or components.

These refactors are listed here so they aren't lost. The quality infrastructure built in Phases 1–6 is specifically what makes them safe to attempt.
