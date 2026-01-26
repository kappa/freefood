# FreeFood Implementation Plan

Version: 2.0
Date: 2026-01-25

## Overview

This plan covers the remaining v1.0 features for FreeFood, organized into logical sections with detailed tasks. Each section builds on previous work.

## Current Status

### Completed
- App structure & authentication flow
- Configuration management (XDG standard)
- Navigation state & history with back button
- Menu bar (Home, Notifications, Directs, Search, Back)
- Feed screen with scrolling and auto-selection
- Post display with body truncation
- Post mode navigation (Enter/Escape, Tab/arrows within post)
- Focusable comments and "more comments" buttons
- Like/unlike posts
- Hide/unhide posts
- API client migrated to v4
- **Section 0: Fix comment display & loading** ✓

### Remaining
- Section 4: Notifications view
- Section 5: Directs view
- Section 6: Compose block (create posts)
- Section 7: Comment creation
- Section 8: Edit posts/comments
- Section 9: Delete posts/comments

---

## Section 0: Fix Comment Display & Loading ✓ COMPLETED

**Priority:** Critical - current behavior is incorrect
**Status:** ✓ Completed (commit 80a8ea2)

**Problem:** Current implementation assumes omitted comments are always at the top ("N earlier comments"). The API provides exact placement via `omittedCommentsOffset`.

**Correct behavior:**
- `omittedCommentsOffset` specifies where the gap is in the comment list
- Example: `comments: [c1, c2, c3]`, `omittedComments: 10`, `omittedCommentsOffset: 1`
- Display: c1, then **[10 more comments with M likes]**, then c2, c3
- Only show button when `omittedComments > 0` (ignore offset otherwise)

### Tasks

**0.1 Update Post model**
- Add `omitted_comments_offset: int` field to Post dataclass
- Parse from API response `omittedCommentsOffset`
- Add `omitted_comment_likes: int` field for button text

**0.2 Fix `_render_comments()` in PostBlock**
- Remove current "first 2 / last 2" logic
- Remove current "N earlier comments" button at top
- Insert "Load more" button at `omittedCommentsOffset` position
- Button text: `"N more comments with M likes"` (using `omittedComments` and `omittedCommentLikes`)
- Display comments in correct order with button at proper position

**0.3 Update expand comments behavior**
- Button click loads full comments via `api.get_post(id)`
- Replace comment list with complete list
- Remove the "load more" button after loading

**0.4 Handle edge cases**
- Only show button when `omittedComments > 0`
- `omittedCommentsOffset: 0` with `omittedComments > 0` → button at very top
- `omittedCommentsOffset` equals comments length → button at bottom
- `omittedComments: 0` → no button, regardless of offset value

**0.5 Update tests**
- Fix existing tests that assume old behavior
- Add tests for offset placement at start, middle, end
- Test that button not shown when `omittedComments: 0`

**Estimated tests:** 6-8

---

## Section 1: Search View

**Priority:** High - simple read-only feature, good foundation

**Status:** ✓ Completed

### Tasks

**1.1 SearchScreen skeleton**
- Create `freefood/screens/search.py`
- Layout: Query input at top, results below using PostBlock
- Empty state: "Enter a search query"
- Loading state while fetching

**1.2 Query input widget**
- Single-line Input widget with placeholder "Search..."
- Submit on Enter key
- Clear button or Escape to clear

**1.3 Wire up menu**
- Search button in MenuBar navigates to SearchScreen
- Pass query to `api.search()`
- Display results as PostBlocks in ScrollableContainer

**1.4 Search state management**
- Add `search_query: str` to AppState
- Persist query when navigating away
- Restore query when returning via Back button

**1.5 Search term highlighting**
- Parse query for search terms (handle quoted phrases)
- In PostBlock, highlight matching terms in post body and comments
- Use Textual Rich markup (e.g., `[reverse]term[/reverse]`)
- Case-insensitive matching

**Estimated tests:** 8-10

---

## Section 2: User/Group Feed Navigation

**Priority:** High - natural follow-up to search, enables browsing

**Status:** ✓ Completed

### Tasks

**2.1 Clickable usernames in post header**
- In PostBlock header (`@alice wrote in @group:`), make usernames clickable
- Post message when clicked: `PostBlock.UserClicked(username, user_type)`
- Visual indication that usernames are clickable (underline or color)

**2.2 FeedScreen handles UserClicked**
- On `UserClicked`, push current view to history stack
- Set `state.current_view = View.USER_FEED` or `View.GROUP_FEED`
- Set `state.current_target = username`
- Call `api.get_user_feed(username)` and display results

**2.3 User feed header**
- When viewing user/group feed, show header with profile info
- Display: `@username - Screen Name`
- Different styling for groups vs users

**2.4 Clickable usernames in comments and likes**
- Comment authors (`-- @bob`) are clickable
- Likes line (`@alice, @bob and 3 others`) - each name clickable
- "N others" could open a likes list (out of scope for v1)

**Estimated tests:** 6-8

---

## Section 3: Subscribe/Unsubscribe

**Priority:** Medium - extends user feed functionality

**Status:** ✓ Completed

### Tasks

**3.1 Subscription state from API**
- When fetching user feed, check subscription status
- API response includes relationship info
- Track whether current user is subscribed to viewed user

**3.2 Subscribe button on user feed header**
- Show `[Subscribe]` or `[Unsubscribe]` button based on state
- Only show for user feeds (not groups - different join flow)
- Position: right side of user feed header

**3.3 Subscribe action**
- Call `api.subscribe(username)`
- Update button label on success
- Show toast: "Subscribed to @username"

**3.4 Unsubscribe action**
- Call `api.unsubscribe(username)`
- Update button label on success
- Show toast: "Unsubscribed from @username"

**3.5 Error handling**
- Handle already subscribed / not subscribed errors gracefully
- Handle private accounts (show message about subscription requests)

**Estimated tests:** 5-6

---

## Section 4: Notifications View

**Priority:** Medium - different layout, important feature

### Tasks

**4.1 NotificationBlock widget**
- Create `freefood/widgets/notification.py`
- Different from PostBlock - shows notification event
- Format varies by `event_type`:
  - `direct_comment`: `@alice commented on your post: "text..."`
  - `post_comment`: `@alice commented on @bob's post: "text..."`
  - `mention_in_post`: `@alice mentioned you: "text..."`
  - `mention_in_comment`: `@alice mentioned you in a comment: "text..."`
  - `post_like`: `@bob liked your post`
  - `subscription`: `@carol subscribed to you`
  - And others as discovered

**4.2 Notification model**
- Add `Notification` dataclass to `models.py`
- Fields: `id`, `event_id`, `event_type`, `date`, `created_user`, `post_id`, `comment_id`
- Parse from API response (key is `Notifications` with capital N)

**4.3 NotificationsScreen**
- Create `freefood/screens/notifications.py`
- Layout: List of NotificationBlocks in ScrollableContainer
- No compose block

**4.4 API integration**
- Add `api.get_notifications()` method
- Denormalize: join user IDs to user objects
- Handle pagination (offset/limit)

**4.5 Clickable elements in notifications**
- Click username → navigate to user feed
- Click post reference → navigate to single post view or scroll to in feed

**4.6 Unread indicator (optional)**
- Show unread count on Notifications menu button
- API provides `unreadNotificationsNumber` in whoami

**Estimated tests:** 8-10

---

## Section 5: Directs View

**Priority:** Medium - similar to home feed with recipient twist

### Tasks

**5.1 Reuse FeedScreen for Directs**
- FeedScreen with `view == View.DIRECTS` conditional
- Calls `api.get_directs()` instead of `api.get_home_feed()`
- Less code duplication than separate screen

**5.2 Menu bar connection**
- Directs button switches to `View.DIRECTS`
- Triggers appropriate API call

**5.3 Unread indicator**
- API returns `unreadDirectsNumber` in whoami response
- Show on Directs menu button: `Directs (3)`
- Update after viewing directs

**5.4 Direct message display**
- Same PostBlock rendering
- Header shows recipients: `@alice → @bob, @carol:`
- No groups in directs

**5.5 Compose for directs (depends on Section 6)**
- ComposeBlock with "To:" field for recipients
- Validate: at least one recipient required
- Recipients are usernames, not group names

**Estimated tests:** 5-6

---

## Section 6: Compose Block - Create Posts

**Priority:** High - core interaction feature

### Tasks

**6.1 ComposeBlock widget**
- Create `freefood/widgets/compose.py`
- Collapsed state: single line "Write something..."
- Expanded state:
  ```
  ┌─────────────────────────────────────────┐
  │ Write something...                      │
  │ █                                       │
  │                                         │
  │ Post to: [feeds]           [Cancel][Post]│
  └─────────────────────────────────────────┘
  ```
- Expands when focused/clicked

**6.2 Multi-line text input**
- Use Textual's `TextArea` widget
- Grows as content is typed
- Arrow keys navigate within text
- Enter inserts newline

**6.3 "Post to" field**
- Input for group/feed names (comma-separated)
- Default: user's own feed (their username)
- For directs: recipient usernames instead

**6.4 Keyboard navigation**
- Tab cycles: TextArea → Post to → Cancel → Post → TextArea
- Ctrl+Enter: submit shortcut
- Escape: cancel/collapse

**6.5 Submit action**
- Validate: body not empty
- Call `api.create_post(body, feeds)`
- On success: clear compose, refresh feed, show toast "Posted!"
- On error: show error toast, keep content for retry

**6.6 Cancel action**
- Clear text fields
- Collapse compose block
- Return focus to feed

**6.7 Placement in screens**
- Show at top of Home feed
- Show in Directs (with recipient field)
- Don't show in Search, Notifications, User feeds

**Estimated tests:** 10-12

---

## Section 7: Comment Creation

**Priority:** High - essential interaction

### Tasks

**7.1 CommentCompose widget**
- Smaller inline compose for comments
- Appears after last comment:
  ```
  │ [7♥] Latest comment... -- @grace              │
  │ ┌───────────────────────────────────────────┐ │
  │ │ Write a comment...                        │ │
  │ │ █                              [Cancel][Submit] │
  │ └───────────────────────────────────────────┘ │
  ```

**7.2 Trigger from Comment button**
- In post mode, Enter on `[Comment]` button
- Shows CommentCompose at bottom of post
- Focus moves to text input

**7.3 Text input behavior**
- Multi-line TextArea (smaller default height)
- Enter inserts newline
- Ctrl+Enter submits

**7.4 Submit action**
- Validate: body not empty
- Call `api.create_comment(post_id, body)`
- On success: add comment to post, hide compose, show toast
- Refresh/recompose to show new comment

**7.5 Cancel action**
- Hide CommentCompose
- Return focus to Comment button

**7.6 Keyboard navigation**
- CommentCompose is part of post mode focus cycle
- Tab from last comment → CommentCompose
- Escape → cancel and close

**7.7 Update post after comment**
- Append new comment to `post.comments`
- New comment is focusable in post mode
- Recompose PostBlock

**Estimated tests:** 8-10

---

## Section 8: Edit Posts & Comments

**Priority:** Medium - completes authoring features

### Tasks

**8.1 Edit button visibility**
- `[Edit]` button only on own posts (`post.is_own == True`)
- `[Edit]` button only on own comments (`comment.is_own == True`)

**8.2 Edit post flow**
- Enter on `[Edit]` button in post mode
- Replace post body with TextArea (pre-filled with current body)
- Show `[Cancel]` `[Save]` buttons
- Ctrl+Enter saves, Escape cancels

**8.3 Edit post submit**
- Call `api.update_post(post_id, new_body)`
- On success: update `post.body`, recompose, toast "Post updated"
- On error: show error, keep editor open

**8.4 Edit post cancel**
- Discard changes
- Return to normal post display
- Focus back to Edit button

**8.5 Edit comment flow**
- Enter on `[Edit]` next to own comment
- Replace comment text with TextArea (pre-filled)
- Show `[Cancel]` `[Save]` inline

**8.6 Edit comment submit**
- Call `api.update_comment(comment_id, new_body)`
- On success: update comment, recompose, toast
- On error: show error, keep editor

**8.7 Edit comment cancel**
- Discard changes
- Return to normal comment display

**Estimated tests:** 8-10

---

## Section 9: Delete Posts & Comments

**Priority:** Medium - completes CRUD

### Tasks

**9.1 Delete button visibility**
- `[Delete]` button only on own posts/comments
- Position: after Edit button

**9.2 Inline confirmation**
- Enter on `[Delete]` → button changes to `[Confirm Delete]` `[Cancel]`
- Must press Confirm to actually delete
- Escape or Cancel returns to normal Delete button

**9.3 Delete post action**
- Call `api.delete_post(post_id)`
- On success: remove PostBlock from feed, toast "Post deleted"
- On error: show error, return to normal state

**9.4 Delete comment action**
- Call `api.delete_comment(comment_id)`
- On success: remove comment from post, recompose, toast
- On error: show error

**9.5 Focus after delete**
- After deleting post: focus moves to next post (or previous if last)
- After deleting comment: focus moves to next focusable in post

**Estimated tests:** 6-8

---

## Implementation Order

Recommended sequence based on dependencies:

1. **Section 0** - Fix comments (foundation)
2. **Section 1** - Search (simple, teaches view patterns)
3. **Section 2** - User/group navigation (extends search utility)
4. **Section 6** - Compose (core feature)
5. **Section 7** - Comment creation (builds on compose)
6. **Section 5** - Directs (uses compose)
7. **Section 4** - Notifications (different layout)
8. **Section 3** - Subscribe (extends user feed)
9. **Section 8** - Edit (extends compose patterns)
10. **Section 9** - Delete (simple, low risk)

---

## Testing Strategy

- Each section includes estimated test count
- Total new tests: ~70-90
- Use TDD: write failing test first, then implement
- Integration tests for screen navigation
- Mock API responses in unit tests

---

## API Endpoints Summary

All endpoints use v4. Key endpoints by section:

| Section | Endpoints |
|---------|-----------|
| 0 | `GET /v4/posts/{id}` (expand comments) |
| 1 | `GET /v4/search?q=` |
| 2 | `GET /v4/timelines/{username}` |
| 3 | `POST /v4/users/{username}/subscribe`, `/unsubscribe` |
| 4 | `GET /v4/notifications` |
| 5 | `GET /v4/timelines/filter/directs` |
| 6 | `POST /v4/posts` |
| 7 | `POST /v4/comments` |
| 8 | `PUT /v4/posts/{id}`, `PUT /v4/comments/{id}` |
| 9 | `DELETE /v4/posts/{id}`, `DELETE /v4/comments/{id}` |
