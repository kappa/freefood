# FreeFood Attachments Design

Date: 2026-01-27

## Overview

Add support for viewing attachments in posts. Users can open attachments in native apps (download + open) or browser (configurable).

## Goals

- Display attachments inline in posts with type-specific icons
- Open attachments in native apps by default
- Config option to open URLs in browser instead
- Focusable attachment buttons in post mode
- View only (no upload support in v1)

## Data Model

### Attachment Dataclass

```python
@dataclass
class Attachment:
    id: str
    file_name: str
    file_size: int
    media_type: str
    url: str
    thumbnail_url: str | None = None
```

### Post Model Change

Add field to `Post` dataclass:

```python
attachments: list[Attachment] = field(default_factory=list)
```

## Display

Attachments render inline after post body as focusable buttons:

```
@alice wrote:
Check out these photos from the trip!

[📷 sunset.jpg] [📷 mountain.png] [📄 notes.pdf]

2h ago
[Comment] [♥ Like] [Hide] [Edit] [Delete]
```

### Type Icons

| Media Type | Icon |
|------------|------|
| image/* | 📷 |
| video/* | 🎬 |
| audio/* | 🎵 |
| application/pdf, text/* | 📄 |
| other | 📎 |

### Filename Truncation

Long filenames truncated to ~20 chars: `very_long_filen....jpg`

## Interaction

- Attachments are focusable in post mode tab cycle
- Position: after post body, before action buttons
- Press Enter to open attachment

## Configuration

Add to `~/.config/freefood/config.ini`:

```ini
[attachments]
open_mode = native   # "native" or "browser"
```

Default: `native`

## Opening Attachments

### Native Mode (default)

1. User presses Enter on attachment
2. Show brief "Downloading..." indicator
3. Download file to temp dir (`/tmp/freefood-{session-id}/filename.jpg`)
4. Call platform opener:
   - Linux: `xdg-open <path>`
   - macOS: `open <path>`
   - Windows: `start "" "<path>"`
5. Native app opens

### Browser Mode

1. User presses Enter on attachment
2. Call platform opener with URL directly
3. Browser opens

## Temp File Management

- Create temp directory on first download: `/tmp/freefood-{session-id}/`
- Reuse files within session (cache by attachment ID)
- Delete directory on clean app exit
- Crashed sessions cleaned by OS eventually

## API Integration

### Response Format

```json
{
  "posts": [{"id": "p1", "attachments": ["att1", "att2"]}],
  "attachments": [
    {"id": "att1", "fileName": "photo.jpg", "mediaType": "image/jpeg"}
  ]
}
```

### Denormalization

Join attachment IDs to `Attachment` objects when parsing posts (same pattern as users/comments).

**Important:** The `url` field is often missing in API responses. The download URL must be constructed as:
`{base_url}/v4/attachments/{id}/original?redirect=`

## Error Handling

| Error | Behavior |
|-------|----------|
| Download fails | Toast: "Failed to download attachment" |
| No default app | OS shows error dialog |
| Missing URL in API | Skip attachment, log warning |

## Files to Create/Modify

| File | Change |
|------|--------|
| `freefood/models.py` | Add `Attachment` dataclass |
| `freefood/api.py` | Parse attachments, denormalize |
| `freefood/config.py` | Add `get_attachment_open_mode()` |
| `freefood/widgets/post.py` | Render attachment buttons, handle Enter |
| `freefood/screens/feed.py` | Handle `AttachmentOpened` message |
| `freefood/attachments.py` | New: download, temp management, platform opener |
| `tests/test_attachments.py` | New test file |

## Testing Strategy

**Unit tests:**
- Attachment model parsing
- Icon selection by media type
- Filename truncation
- Config parsing

**Widget tests:**
- Attachment buttons render
- Focusable in post mode
- Tab order correct
- Enter emits message

**Integration (manual):**
- Download + native open on Linux
- Browser mode works
- Temp cleanup on exit

**Estimated:** 10-15 new tests

## Out of Scope

- Upload attachments
- Inline image preview in TUI
- Video/audio playback in TUI
- Thumbnail display
