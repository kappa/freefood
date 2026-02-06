# FreeFood Packaging Design

Date: 2026-01-27

## Overview

Create standalone single-file executables for macOS, Windows, and Linux using PyInstaller and GitHub Actions.

## Goals

- Portable executables that don't require Python installed
- All three platforms: Linux, macOS, Windows
- Automated builds via GitHub Actions
- Download artifacts from GitHub UI (no package managers)

## Architecture

### Build Tool: PyInstaller

- Most mature tool for Python standalone executables
- Single-file mode (`--onefile`) for clean distribution
- Must build on target platform (no cross-compilation)

### CI/CD: GitHub Actions

- Runs builds on `ubuntu-latest`, `macos-latest`, `windows-latest`
- Uploads executables as workflow artifacts
- Triggered manually or on version tags

### Output Format

| Platform | Format | Size (est.) |
|----------|--------|-------------|
| Linux | ELF binary | ~15-25 MB |
| macOS | Mach-O binary | ~20-30 MB |
| Windows | `.exe` file | ~20-30 MB |

These are portable executables - no installation required. Users download and run directly from terminal.

## Files to Create

```
freefood/
├── .github/
│   └── workflows/
│       └── build.yml         # GitHub Actions workflow
├── freefood.spec             # PyInstaller spec file
└── pyproject.toml            # (modify) Add pyinstaller dev dependency
```

## PyInstaller Configuration

Key settings for `freefood.spec`:

- Entry point: `freefood/__main__.py`
- `console=True` - Essential for TUI apps
- `upx=True` - Compress executable
- No bundled data files needed
- No hidden imports expected (Textual/httpx are well-behaved)

## GitHub Actions Workflow

### Triggers

- `workflow_dispatch` - Manual trigger from GitHub UI
- `push: tags: ['v*']` - Automatic on version tags

### Jobs

Three parallel jobs, one per platform:

1. **build-linux** on `ubuntu-latest`
2. **build-macos** on `macos-latest`
3. **build-windows** on `windows-latest`

### Steps per Job

1. Checkout code
2. Set up Python 3.11
3. Install dependencies + PyInstaller
4. Run PyInstaller with spec file
5. Upload artifact

### Artifacts

- `freefood-linux` - Linux ELF binary
- `freefood-macos` - macOS Mach-O binary
- `freefood-windows` - Windows .exe

Retained for 90 days (GitHub default).

## User Experience

### Building (developer)

1. Push to GitHub or trigger workflow manually
2. Wait for Actions to complete (~2-5 minutes)
3. Download artifacts from Actions tab

### Using (end user)

Linux/macOS:
```bash
chmod +x freefood
./freefood
```

Windows:
```
freefood.exe
```

Config files still go to standard platform locations:
- Linux: `~/.config/freefood/`
- macOS: `~/Library/Application Support/freefood/`
- Windows: `%APPDATA%\freefood\`

## Testing Strategy

1. Build locally on Linux first to verify PyInstaller works
2. Push to GitHub, verify all three platform builds succeed
3. Download and test each artifact on respective platform (or VM)

## Future Enhancements (out of scope)

- AppImage for Linux
- `.dmg` for macOS
- Native package managers (Homebrew, winget, AUR)
- Auto-update mechanism
- Code signing (macOS/Windows)
