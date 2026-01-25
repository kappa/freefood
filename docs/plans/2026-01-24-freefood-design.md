# FreeFood Console Client - Design Document

Version: 1.0
Date: 2026-01-24

## Overview

FreeFood is a cross-platform console client for the FreeFeed.net social network. It provides a full-screen terminal UI for daily use: reading feeds, posting, commenting, and basic social interactions. Advanced features are delegated to the web interface.

## Goals

- Full interaction for common daily tasks
- Cross-platform: Linux, macOS, Windows
- Keyboard-driven, accessible navigation
- Simple, focused feature set

## Feature Set

### In Scope (v1.0)

| Category | Features |
|----------|----------|
| Reading | Home feed, user timelines, group feeds, notifications, direct messages |
| Posting | Create, edit, delete own posts |
| Commenting | Create, edit, delete own comments |
| Reacting | Like/unlike posts and comments |
| Social | View profiles, subscribe/unsubscribe |
| Search | Simple text query |
| Navigation | History stack with back button |

### Out of Scope

- Bookmarks/saved posts
- Complex search UI (operators work, but no dedicated form)
- Real-time updates / WebSocket
- File attachments (view only, no upload)
- Group management (create, admin functions)
- User profile editing
- Auto-refresh / polling

---

## Architecture

### Three-Layer Design

```
┌─────────────────────────────────────────┐
│              UI Layer                   │
│  (Rendering, input handling, widgets)   │
├─────────────────────────────────────────┤
│            State Layer                  │
│  (Views, navigation, denormalized data) │
├─────────────────────────────────────────┤
│             API Layer                   │
│  (HTTP client, auth, normalization)     │
└─────────────────────────────────────────┘
                   │
                   ▼
           FreeFeed Server
```

### Data Flow

```
User Input → UI Layer → State Layer → API Layer → FreeFeed Server
                ↑                          │
            Render  ←──── State Update ←───┘
```

### Key Data Structures

**Post**
- id, body, createdAt, updatedAt
- author (User)
- groups (list of Users with type=group)
- likes (list of Users)
- comments (list of Comments)
- omittedComments, omittedLikes counts
- isLiked, isHidden (current user's state)

**Comment**
- id, body, createdAt, updatedAt
- author (User)
- likes count
- isLiked (current user's state)

**User**
- id, username, screenName
- type ("user" or "group")
- profilePictureUrl

**View** (enum)
- Home, Notifications, Directs, Search, UserFeed, GroupFeed

**NavigationState**
- currentView
- historyStack (list of previous views with scroll positions)
- focusState (mode, selectedIndex, etc.)

---

## User Interface

### Screen Layout

```
┌─────────────────────────────────────────────────────────────┐
│ [← Back] [Home] [Notifications] [Directs] [Search]    [F5] │
├─────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Write something...                                      │ │
│ │ Post to: [ ]                              [Post]        │ │
│ └─────────────────────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ @alice wrote in @group1, @group2:                       │ │
│ │ Post body text here...                                  │ │
│ │ 2h ago -- [Comment] [♥ Like] [Hide]                     │ │
│ │ @bob, @carol and 5 others liked this                    │ │
│ │ [3♥] First comment... -- @dave                          │ │
│ │ [0♥] Second comment... -- @eve                          │ │
│ │         ── 12 more comments (45 likes) ──               │ │
│ │ [1♥] Recent comment... -- @frank                        │ │
│ │ [7♥] Latest comment... -- @grace                        │ │
│ └─────────────────────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ @henry wrote:                                           │ │
│ │ Another post...                                         │ │
└─────────────────────────────────────────────────────────────┘
```

### Components

**Menu Bar**
- Always visible at top
- Items: Back, Home, Notifications, Directs, Search
- F5 indicator for manual refresh

**Compose Block**
- Appears at top of feed views (Home, Directs)
- Collapsed by default, expands when selected
- Contains: text area, "Post to" input (groups/recipients), Post button

**Post Block**
- Header: `@username wrote in @group1, @group2:`
- Body: Full text, truncated at 50 lines with "show more"
- Action bar: timestamp, Comment, Like/Unlike, Hide/Unhide, Edit*, Delete*
- Likes line: `@user1, @user2 and N others liked this`
- Comments: First 2, expander for middle, last 2
- (* Edit/Delete only shown on own posts)

**Comment**
- Format: `[N♥] comment text... -- @author [Edit] [Delete]`
- Truncated at 10 lines with "show more"
- Edit/Delete only on own comments

**Notification Block**
- Various formats depending on type:
  - `@user replied to your post: [comment text]`
  - `@user mentioned your post in their post: [post text]`
  - `@user subscribed to you`
- Clickable usernames and post references

---

## Navigation

### Three Modes

| Mode | Enter via | Exit via | Up/Down selects |
|------|-----------|----------|-----------------|
| Menu | Escape from Feed | Enter loads view | Menu items |
| Feed | Enter from Menu, Escape from Post | Escape to Menu, Enter to Post | Whole posts |
| Post | Enter from Feed | Escape to Feed | Interactive elements |

### Key Bindings

| Key | Menu Mode | Feed Mode | Post Mode |
|-----|-----------|-----------|-----------|
| ↑/↓ | Select menu item | Select post | Select element |
| ←/→ | Select menu item | - | - |
| Tab | Select menu item | - | Next element |
| Enter | Load selected view | Enter post mode | Activate element |
| Escape | - | Go to menu | Go to feed |
| F5 | Refresh | Refresh | Refresh |

### Post Mode Focus Order

When entering a post, arrow keys cycle through:

1. "Show more" (if post truncated)
2. [Comment] button
3. [♥ Like] button
4. [Hide] button
5. [Edit] button (if own post)
6. [Delete] button (if own post)
7. First comment: [♥] → "show more" (if truncated) → [Edit]/[Delete] (if own)
8. Second comment: same pattern
9. "N more comments" expander (if middle hidden)
10. Second-to-last comment: same pattern
11. Last comment: same pattern

### Navigation History

- Each navigation action pushes to history stack:
  - Switching views (Home → Notifications)
  - Opening user/group feed
  - Opening post from notification
- Back button pops from stack, restores scroll position
- History has reasonable max depth (e.g., 50 entries)

---

## Post Display Rules

### Post Body Truncation

- Show full text up to 50 lines
- Beyond 50 lines: truncate and show "show more" link
- "Show more" expands text inline (no separate view)

### Comment Display

- Each comment truncated at 10 lines with "show more"
- Always show: first 2 comments and last 2 comments
- Middle comments: collapsed under "N more comments (M likes)"
- Clicking expander loads and shows all middle comments inline

### Likes Display

- Show up to 3 usernames: `@alice, @bob, @carol`
- If more: `@alice, @bob, @carol and 42 others liked this`
- Usernames are clickable (navigate to their feed)

---

## Inline Editor

### Appearance

For new comment (appears after last comment):
```
│ [7♥] Latest comment... -- @grace                            │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Type your comment here...                               │ │
│ │ █                                                       │ │
│ │                           [Cancel]  [Submit]            │ │
│ └─────────────────────────────────────────────────────────┘ │
```

For new post (compose block at top):
```
┌─────────────────────────────────────────────────────────────┐
│ Write your post here...                                     │
│ █                                                           │
│                                                             │
│ Post to: [group1, group2]               [Cancel]  [Post]    │
└─────────────────────────────────────────────────────────────┘
```

### Behavior

- Multi-line text input, grows as needed
- Arrow keys navigate within text
- Tab cycles: Text → Cancel → Submit → Text
- Enter: insert newline
- Ctrl+Enter: submit (shortcut)
- Escape: cancel (shortcut)

### Edit Mode

- Same editor, pre-filled with existing text
- Submit updates the post/comment

---

## Views

### Home Feed

- Compose block at top
- Posts from subscriptions, sorted by recent activity
- Standard post blocks

### User/Group Feed

- No compose block (or compose with that group pre-filled for groups)
- Posts by/in that user/group
- Header showing profile info (username, screen name)

### Notifications

- Different layout: notification blocks instead of posts
- Types: replies, mentions, subscriptions, likes
- Clickable elements navigate to relevant content

### Directs

- Same as Home feed
- Shows only direct messages
- Compose block's "Post to" accepts usernames (recipients)

### Search

- Query input at top (persists between visits)
- Results as standard post blocks
- Matched text highlighted in results
- Empty state: "Enter a search query above"

---

## Authentication

### First Run Flow

1. App starts, checks for config file
2. No token → show welcome message
3. Open browser to magic link:
   ```
   https://freefeed.net/settings/app-tokens/create?title=FreeFood%20(Console%20Client)&scopes=read-my-info%20read-my-files%20read-feeds%20read-users-info%20read-realtime%20manage-my-files%20manage-notifications%20manage-posts%20manage-my-feeds%20manage-profile%20manage-groups%20manage-subscription-requests
   ```
4. Prompt: "Paste your token here:"
5. Validate token via `GET /v2/users/whoami`
6. Save to config file
7. Proceed to Home feed

### Token Expiry

- On 401 response: show "Session expired" message
- Prompt to re-authenticate (repeat browser flow)

---

## Configuration

### File Location (XDG Standard)

- Linux: `~/.config/freefood/config.ini`
- macOS: `~/Library/Application Support/freefood/config.ini`
- Windows: `%APPDATA%\freefood\config.ini`

### File Format (INI)

```ini
[auth]
token = eyJhbGciOiJIUzI1NiIs...

[user]
username = kappa
```

---

## Loading & Error States

### Loading

Display inline where content would appear:
```
              Loading home feed...
```

### Errors

Display inline with retry hint:
```
              ⚠ Failed to load feed: Connection timeout
              Press F5 to retry
```

### Refresh

- F5 reloads current view
- No auto-refresh or polling

---

## API Endpoints

| Operation | Method | Endpoint |
|-----------|--------|----------|
| Validate token | GET | `/v2/users/whoami` |
| Home feed | GET | `/v2/timelines/home` |
| User timeline | GET | `/v2/timelines/{username}` |
| Notifications | GET | `/v2/notifications` |
| Directs | GET | `/v2/timelines/filter/directs` |
| Search | GET | `/v2/search?q={query}` |
| Single post | GET | `/v2/posts/{id}?maxComments=all` |
| Create post | POST | `/v2/posts` |
| Update post | PUT | `/v2/posts/{id}` |
| Delete post | DELETE | `/v2/posts/{id}` |
| Like post | POST | `/v2/posts/{id}/like` |
| Unlike post | POST | `/v2/posts/{id}/unlike` |
| Hide post | POST | `/v2/posts/{id}/hide` |
| Unhide post | POST | `/v2/posts/{id}/unhide` |
| Create comment | POST | `/v2/comments` |
| Update comment | PUT | `/v2/comments/{id}` |
| Delete comment | DELETE | `/v2/comments/{id}` |
| Like comment | POST | `/v2/comments/{id}/like` |
| Unlike comment | POST | `/v2/comments/{id}/unlike` |
| Subscribe | POST | `/v2/users/{username}/subscribe` |
| Unsubscribe | POST | `/v2/users/{username}/unsubscribe` |

### Denormalization

API returns normalized data with separate arrays for posts, comments, users. The client must join references:

- `post.createdBy` → user object
- `post.comments` → comment objects
- `comment.createdBy` → user object
- `post.postedTo` → feed/group objects

### Response Format Variations

**Important:** The structure of `posts` in API responses varies by endpoint:

| Endpoint Type | `posts` field type |
|---------------|-------------------|
| Timeline endpoints (`/v2/timelines/*`, `/v2/search`) | **List** of post objects |
| Single post endpoint (`/v2/posts/{id}`) | **Single dict** (not a list) |
| `/v2/users/whoami` | `users` is a **single dict** (not a list) |

Example: For `/v2/posts/{id}`:
```json
{
  "posts": {"id": "abc", "body": "...", ...},  // dict, NOT a list
  "comments": [...],
  "users": [...]
}
```

**Note:** API documentation is unofficial/discovered. Verify during implementation and update this document with corrections.

---

## Future Considerations

Not in v1.0, but may be added later:

- Attachment viewing (images inline or via external viewer)
- Real-time updates via WebSocket
- Keyboard shortcut customization
- Color theme customization
- Mouse support (Textual supports it)
- Offline mode / caching
