# FreeFood Packaging Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Set up PyInstaller builds via GitHub Actions to produce standalone executables for Linux, macOS, and Windows.

**Architecture:** PyInstaller bundles Python + dependencies into single-file executables. GitHub Actions runs builds on all three platforms in parallel. Artifacts are downloadable from the Actions tab.

**Tech Stack:** PyInstaller, GitHub Actions, Python 3.11+

**Design doc:** `docs/plans/2026-01-27-packaging-design.md`

---

## Task 1: Add PyInstaller Dependency

**Files:**
- Modify: `pyproject.toml`

**Step 1: Add pyinstaller to dev dependencies**

Edit `pyproject.toml`, change the `[project.optional-dependencies]` section:

```toml
[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
    "pyinstaller>=6.0",
]
```

**Step 2: Install the new dependency**

Run:
```bash
/home/kappa/work/frf/freefood/.venv/bin/pip install -e ".[dev]"
```

Expected: PyInstaller installs successfully

**Step 3: Verify PyInstaller is available**

Run:
```bash
/home/kappa/work/frf/freefood/.venv/bin/pyinstaller --version
```

Expected: Version 6.x.x printed

**Step 4: Commit**

```bash
git add pyproject.toml
git commit -m "build: add pyinstaller dev dependency"
```

---

## Task 2: Create PyInstaller Spec File

**Files:**
- Create: `freefood.spec`

**Step 1: Create the spec file**

Create `freefood.spec` in the project root:

```python
# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec file for FreeFood."""

a = Analysis(
    ['freefood/__main__.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='freefood',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
```

**Step 2: Test local build**

Run:
```bash
cd /home/kappa/work/frf/freefood
/home/kappa/work/frf/freefood/.venv/bin/pyinstaller freefood.spec --distpath build --workpath build/work --clean
```

Expected: Build completes, creates `build/freefood` executable

**Step 3: Test the executable**

Run:
```bash
./build/freefood --help 2>&1 || ./build/freefood &
sleep 2
pkill -f "build/freefood" 2>/dev/null || true
echo "Executable runs"
```

Expected: App starts (or shows help). Kill it since it's interactive.

**Step 4: Add build directory to gitignore**

Check if `build/` is already in `.gitignore`. If not, add it:

```bash
echo "build/" >> .gitignore
```

**Step 5: Commit**

```bash
git add freefood.spec .gitignore
git commit -m "build: add PyInstaller spec file"
```

---

## Task 3: Create GitHub Actions Workflow Directory

**Files:**
- Create: `.github/workflows/` directory

**Step 1: Create the directory structure**

Run:
```bash
mkdir -p /home/kappa/work/frf/freefood/.github/workflows
```

**Step 2: Verify**

Run:
```bash
ls -la /home/kappa/work/frf/freefood/.github/workflows
```

Expected: Empty directory exists

---

## Task 4: Create GitHub Actions Build Workflow

**Files:**
- Create: `.github/workflows/build.yml`

**Step 1: Create the workflow file**

Create `.github/workflows/build.yml`:

```yaml
name: Build Executables

on:
  workflow_dispatch:  # Manual trigger
  push:
    tags:
      - 'v*'  # Trigger on version tags

jobs:
  build:
    strategy:
      matrix:
        include:
          - os: ubuntu-latest
            artifact_name: freefood
            asset_name: freefood-linux
          - os: macos-latest
            artifact_name: freefood
            asset_name: freefood-macos
          - os: windows-latest
            artifact_name: freefood.exe
            asset_name: freefood-windows.exe

    runs-on: ${{ matrix.os }}

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev]"

      - name: Build executable
        run: |
          pyinstaller freefood.spec --distpath dist --workpath build --clean

      - name: Upload artifact
        uses: actions/upload-artifact@v4
        with:
          name: ${{ matrix.asset_name }}
          path: dist/${{ matrix.artifact_name }}
          retention-days: 90
```

**Step 2: Validate YAML syntax**

Run:
```bash
python -c "import yaml; yaml.safe_load(open('.github/workflows/build.yml'))" 2>&1 || echo "Install pyyaml or skip validation"
```

Expected: No errors (or pyyaml not installed, which is fine)

**Step 3: Commit**

```bash
git add .github/workflows/build.yml
git commit -m "ci: add GitHub Actions workflow for building executables"
```

---

## Task 5: Test Workflow Locally (Optional Validation)

**Files:**
- None (validation only)

**Step 1: Verify workflow file exists and is valid**

Run:
```bash
cat /home/kappa/work/frf/freefood/.github/workflows/build.yml | head -20
```

Expected: Shows the workflow YAML

**Step 2: Verify local build still works**

Run:
```bash
cd /home/kappa/work/frf/freefood
/home/kappa/work/frf/freefood/.venv/bin/pyinstaller freefood.spec --distpath dist --workpath build --clean
ls -lh dist/freefood
```

Expected: Executable exists, shows size (~15-25 MB)

**Step 3: Clean up local build artifacts**

Run:
```bash
rm -rf /home/kappa/work/frf/freefood/dist /home/kappa/work/frf/freefood/build
```

---

## Task 6: Update Gitignore and Final Commit

**Files:**
- Modify: `.gitignore`

**Step 1: Ensure build artifacts are ignored**

Verify `.gitignore` contains these entries (add if missing):

```
build/
dist/
*.spec.bak
```

**Step 2: Commit if changes were made**

```bash
git add .gitignore
git diff --cached --quiet || git commit -m "build: update gitignore for PyInstaller artifacts"
```

**Step 3: Push to GitHub**

```bash
git push origin main
```

---

## Task 7: Trigger and Verify GitHub Actions Build

**Files:**
- None (GitHub UI)

**Step 1: Go to GitHub Actions**

Open: `https://github.com/<username>/freefood/actions`

**Step 2: Trigger manual build**

1. Click "Build Executables" workflow
2. Click "Run workflow" button
3. Select `main` branch
4. Click "Run workflow"

**Step 3: Wait for builds to complete**

Expected: All three jobs (Linux, macOS, Windows) complete successfully (~2-5 minutes)

**Step 4: Download and verify artifacts**

1. Click on the completed workflow run
2. Scroll to "Artifacts" section
3. Download each artifact:
   - `freefood-linux`
   - `freefood-macos`
   - `freefood-windows.exe`

**Step 5: Test Linux artifact locally**

```bash
chmod +x freefood-linux/freefood
./freefood-linux/freefood &
sleep 2
pkill -f freefood || true
echo "Linux build works"
```

---

## Summary

After completing all tasks:

1. PyInstaller is configured via `freefood.spec`
2. GitHub Actions builds executables for all three platforms
3. Artifacts are downloadable from the Actions tab
4. Manual trigger via `workflow_dispatch` or automatic on version tags (`v*`)

**To release a new version:**

```bash
git tag v0.1.0
git push origin v0.1.0
```

This triggers the build workflow and creates downloadable artifacts.
