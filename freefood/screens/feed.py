"""Feed screen for displaying posts."""

from textual.app import ComposeResult
from textual.containers import ScrollableContainer
from textual.widgets import Button, Collapsible, Static

from freefood.config import get_username
from freefood.models import Post, View
from freefood.screens.base import BaseScreen
from freefood.state import AppState
from freefood.widgets.comment_compose import CommentCompose
from freefood.widgets.compose import ComposeBlock
from freefood.widgets.menu import MenuBar
from freefood.widgets.post import PostBlock


class FeedContainer(ScrollableContainer):
    """ScrollableContainer that auto-moves selection when focused post scrolls out."""

    def watch_scroll_y(self, old_value: float, new_value: float) -> None:
        """When scroll position changes, check if focused post is still visible."""
        super().watch_scroll_y(old_value, new_value)
        # Use set_timer to run the check after layout completes
        # A small delay ensures the layout is updated
        self.set_timer(0.01, self._check_focused_visibility)

    def _check_focused_visibility(self) -> None:
        """Check if focused widget is visible, move selection if not."""
        focused = self.app.focused
        if focused is None or not isinstance(focused, PostBlock):
            return

        # Check if focused post is in post_mode - don't auto-move if so
        if focused.post_mode:
            return

        # Check if focused widget is visible in this container's viewport
        if not self._is_widget_visible(focused):
            self._move_focus_to_visible_post()

    def _is_widget_visible(self, widget: PostBlock) -> bool:
        """Check if a widget is visible within this container's viewport."""
        # Get the widget's region relative to the container
        widget_region = widget.region

        # Check if the widget's region intersects with the visible viewport
        # The widget needs to be at least partially visible
        container_top = self.region.y
        container_bottom = container_top + self.region.height

        widget_top = widget_region.y
        widget_bottom = widget_top + widget_region.height

        # Widget is visible if any part of it is within the container's viewport
        return widget_bottom > container_top and widget_top < container_bottom

    def _move_focus_to_visible_post(self) -> None:
        """Move focus to a visible PostBlock."""
        # Find the first visible PostBlock using screen regions
        container_top = self.region.y
        container_bottom = container_top + self.region.height

        for post_block in self.query(PostBlock):
            widget_region = post_block.region
            widget_top = widget_region.y
            widget_bottom = widget_top + widget_region.height

            # Check if widget is at least partially visible
            if widget_bottom > container_top and widget_top < container_bottom:
                post_block.focus()
                return


class FeedScreen(BaseScreen):
    """Screen for displaying feed content."""

    BINDINGS = [
        ("escape", "focus_menu", "Menu"),
        ("enter", "focus_feed", "Feed"),
        ("f5", "refresh", "Refresh"),
    ]

    CSS = """
    FeedScreen {
        layout: vertical;
    }

    #feed-container {
        height: 1fr;
        padding: 0 1;
    }

    #feed-header {
        text-style: bold;
        margin: 0 0 1 0;
        width: 100%;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    #btn-subscribe {
        height: 1;
        padding: 0 1;
        border: none;
        margin: 0 0 1 0;
        min-width: 12;
        background: transparent;
        color: $accent;
        text-style: underline;
    }

    #error-banner {
        background: $error;
        color: $text;
        padding: 0 1;
        display: none;
    }

    #error-banner.visible {
        display: block;
    }
    """

    def __init__(self, state: AppState | None = None) -> None:
        """Initialize feed screen."""
        super().__init__()
        self._state = state  # Will use app.state if None
        self.posts: list[Post] = []
        self.is_subscribed: bool = False

    @property
    def state(self) -> AppState:
        """Get app state."""
        if self._state is not None:
            return self._state
        return self.app.state

    def compose(self) -> ComposeResult:
        """Create feed screen widgets."""
        yield MenuBar(self.state.current_view)
        yield Static("", id="error-banner")
        with FeedContainer(id="feed-container"):
            yield Static("Loading feed...", classes="loading")

    async def on_mount(self) -> None:
        """Load feed on mount."""
        await self.refresh_content()

    async def refresh_content(self) -> None:
        """Refresh feed content."""
        container = self.query_one("#feed-container")
        container.remove_children()
        container.mount(Static("Loading feed...", classes="loading"))

        try:
            api = self.app.api
            if api is None:
                raise Exception("Not connected")

            if self.state.current_view == View.HOME:
                self.posts = await api.get_home_feed()
            elif self.state.current_view == View.DIRECTS:
                self.posts = await api.get_directs()
            elif self.state.current_view in (View.USER_FEED, View.GROUP_FEED):
                if self.state.current_target:
                    self.posts = await api.get_user_feed(self.state.current_target)
                else:
                    self.posts = []
            else:
                self.posts = []

            container.remove_children()

            try:
                count = await api.get_unread_notifications_count()
                menu = self.query_one(MenuBar)
                menu.set_notifications_count(count)
            except Exception:
                pass

            try:
                count = await api.get_unread_directs_count()
                menu = self.query_one(MenuBar)
                menu.set_directs_count(count)
            except Exception:
                pass

            # Show compose block for HOME and DIRECTS views
            if self.state.current_view in (View.HOME, View.DIRECTS):
                default_feeds = get_username() or ""
                container.mount(ComposeBlock(default_feeds=default_feeds))

            if self.state.current_view in (View.USER_FEED, View.GROUP_FEED):
                if self.state.current_target:
                    header_text = self._feed_header_text(self.posts)
                    container.mount(Static(header_text, id="feed-header"))
                    if self.state.current_view == View.USER_FEED:
                        self.is_subscribed = await api.get_user_subscription_status(
                            self.state.current_target
                        )
                        label = "Unsubscribe" if self.is_subscribed else "Subscribe"
                        container.mount(Button(label, id="btn-subscribe"))

            if not self.posts:
                container.mount(Static("No posts found", classes="loading"))
            else:
                self._mount_post_blocks(container)

        except Exception as e:
            container.remove_children()
            container.mount(
                Static(f"Failed to load: {e}\nPress F5 to retry", classes="error")
            )

    def _feed_header_text(self, posts: list[Post]) -> str:
        """Build header text for user/group feeds."""
        target = self.state.current_target or ""
        screen_name = None

        if self.state.current_view == View.USER_FEED:
            for post in posts:
                if post.author and post.author.username == target:
                    screen_name = post.author.screen_name
                    break
        elif self.state.current_view == View.GROUP_FEED:
            for post in posts:
                for group in post.groups:
                    if group.username == target:
                        screen_name = group.screen_name
                        break
                if screen_name:
                    break

        if screen_name and screen_name != target:
            return f"@{target} - {screen_name}"
        return f"@{target}"

    def _mount_post_blocks(self, container) -> None:
        """Mount post blocks, grouping hidden posts in home feed."""
        if self.state.current_view == View.HOME:
            visible_posts = [p for p in self.posts if not p.is_hidden]
            hidden_posts = [p for p in self.posts if p.is_hidden]

            for post in visible_posts:
                container.mount(PostBlock(post, show_hide_button=True))

            if hidden_posts:
                count = len(hidden_posts)
                label = f"Hidden {count} post{'s' if count != 1 else ''}"
                hidden_blocks = [
                    PostBlock(post, show_hide_button=True) for post in hidden_posts
                ]
                collapsible = Collapsible(
                    *hidden_blocks,
                    title=label,
                    collapsed=True,
                )
                container.mount(collapsible)
        else:
            for post in self.posts:
                container.mount(PostBlock(post, show_hide_button=False))

        first_post = next(iter(container.query(PostBlock)), None)
        if first_post:
            first_post.focus()

    def _rebuild_feed_layout(self) -> None:
        """Rebuild post layout while preserving header/compose widgets."""
        container = self.query_one("#feed-container")
        for block in list(container.query(PostBlock)):
            block.remove()
        for collapsible in list(container.query(Collapsible)):
            collapsible.remove()
        for loading in list(container.query("Static.loading")):
            loading.remove()

        if not self.posts:
            container.mount(Static("No posts found", classes="loading"))
            return

        self._mount_post_blocks(container)

    def _focus_button_in_post_block(self, block: PostBlock, button_id: str) -> None:
        """Focus a button in a post block after a recompose, if it exists."""
        try:
            button = block.query_one(f"#{button_id}", Button)
            button.focus()
        except Exception:
            pass

    def action_focus_menu(self) -> None:
        """Focus the menu bar."""
        focused = self.app.focused
        post_block = self._find_post_block(focused)
        if post_block is not None and post_block.post_mode:
            post_block.action_exit_post_mode()
            return

        menu = self.query_one(MenuBar)
        menu.focus_current_view_button()

    def action_focus_feed(self) -> None:
        """Focus the feed (first post)."""
        container = self.query_one("#feed-container")
        first_post = container.query(PostBlock).first()
        if first_post:
            first_post.focus()

    def _find_post_block(self, widget) -> PostBlock | None:
        """Find nearest PostBlock ancestor for a focused widget."""
        current = widget
        while current is not None:
            if isinstance(current, PostBlock):
                return current
            current = current.parent
        return None

    def action_refresh(self) -> None:
        """Refresh feed."""
        self.run_worker(self.refresh_content())

    def on_menu_bar_view_selected(self, message: MenuBar.ViewSelected) -> None:
        """Handle view change from menu."""
        if message.view == View.SEARCH:
            if self.state.current_view != View.SEARCH:
                self.state.navigate_to(View.SEARCH)
            from freefood.screens.search import SearchScreen

            self.app.push_screen(SearchScreen(self.state))
            return
        if message.view == View.NOTIFICATIONS:
            if self.state.current_view != View.NOTIFICATIONS:
                self.state.navigate_to(View.NOTIFICATIONS)
            from freefood.screens.notifications import NotificationsScreen

            self.app.push_screen(NotificationsScreen(self.state))
            return
        if message.view == View.ERRORS:
            if self.state.current_view != View.ERRORS:
                self.state.navigate_to(View.ERRORS)
            from freefood.screens.errors import ErrorsScreen

            self.app.push_screen(ErrorsScreen())
            return

        if message.view != self.state.current_view:
            self.state.navigate_to(message.view)
            menu = self.query_one(MenuBar)
            menu.set_view(message.view)
        self.run_worker(self.refresh_content())

    def on_menu_bar_back_requested(self, message: MenuBar.BackRequested) -> None:
        """Handle back request."""
        entry = self.state.pop_history()
        if entry:
            self.state.current_view = entry.view
            self.state.current_target = entry.target
            if entry.query:
                self.state.search_query = entry.query
            if entry.view == View.SEARCH:
                from freefood.screens.search import SearchScreen

                self.app.push_screen(SearchScreen(self.state))
            else:
                menu = self.query_one(MenuBar)
                menu.set_view(entry.view)
                self.run_worker(self.refresh_content())
                # TODO: Restore scroll_position after content loads
        else:
            self.notify("No history")

    async def on_post_block_expand_comments(
        self, message: PostBlock.ExpandComments
    ) -> None:
        """Load full comments for a post."""
        try:
            full_post = await self.app.api.get_post(message.post.id)
            if full_post:
                # Find and update the PostBlock
                for block in self.query(PostBlock):
                    if block.post.id == message.post.id:
                        block.post = full_post
                        block.comments_expanded = True
                        block.refresh(recompose=True)
                        focus_index = 0
                        if message.post.omitted_comments > 0:
                            focus_index = message.post.omitted_comments_offset
                        self.app.set_timer(
                            0.05,
                            lambda b=block, f=focus_index: b.focus_comment_at(f),
                        )
                        break
        except Exception as e:
            self.show_error("Failed to load comments", e)

    async def on_post_block_like_requested(
        self, message: PostBlock.LikeRequested
    ) -> None:
        """Handle like/unlike request."""
        post = message.post
        try:
            if post.is_liked:
                await self.app.api.unlike_post(post.id)
                post.is_liked = False
                current_user = self.app.api.current_user
                if current_user is not None:
                    post.likes = [u for u in post.likes if u.id != current_user.id]
                self.notify("Unliked")
            else:
                await self.app.api.like_post(post.id)
                post.is_liked = True
                current_user = self.app.api.current_user
                if current_user is not None:
                    post.likes.insert(0, current_user)
                self.notify("Liked")
            # Refresh the post block
            for block in self.query(PostBlock):
                if block.post.id == post.id:
                    block.refresh(recompose=True)
                    break
        except Exception as e:
            self.show_error("Like/unlike failed", e)

    async def on_post_block_hide_requested(
        self, message: PostBlock.HideRequested
    ) -> None:
        """Handle hide/unhide request."""
        post = message.post
        try:
            if post.is_hidden:
                await self.app.api.unhide_post(post.id)
                post.is_hidden = False
                self.notify("Unhidden")
            else:
                await self.app.api.hide_post(post.id)
                post.is_hidden = True
                self.notify("Hidden")
            self._rebuild_feed_layout()
        except Exception as e:
            self.show_error("Hide/unhide failed", e)

    async def on_post_block_comment_like_requested(
        self, message: PostBlock.CommentLikeRequested
    ) -> None:
        """Handle comment like/unlike request."""
        comment = message.comment
        try:
            if comment.is_liked:
                await self.app.api.unlike_comment(comment.id)
                comment.is_liked = False
                comment.likes = max(0, comment.likes - 1)
                self.notify("Comment unliked")
            else:
                await self.app.api.like_comment(comment.id)
                comment.is_liked = True
                comment.likes += 1
                self.notify("Comment liked")

            for block in self.query(PostBlock):
                for block_comment in block.post.comments:
                    if block_comment.id == comment.id:
                        block.refresh(recompose=True)
                        self.set_timer(
                            0.05,
                            lambda b=block, c=comment: self._focus_button_in_post_block(
                                b, f"comment-like-{c.id}"
                            ),
                        )
                        return
        except Exception as e:
            self.show_error("Comment like/unlike failed", e)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle subscribe/unsubscribe button."""
        if event.button.id != "btn-subscribe":
            return

        if self.state.current_target is None:
            return

        try:
            if self.is_subscribed:
                await self.app.api.unsubscribe(self.state.current_target)
                self.is_subscribed = False
                event.button.label = "Subscribe"
                self.notify(f"Unsubscribed from @{self.state.current_target}")
            else:
                await self.app.api.subscribe(self.state.current_target)
                self.is_subscribed = True
                event.button.label = "Unsubscribe"
                self.notify(f"Subscribed to @{self.state.current_target}")
        except Exception as e:
            self.show_error("Subscribe/unsubscribe failed", e)

    async def on_post_block_user_clicked(self, message: PostBlock.UserClicked) -> None:
        """Handle navigation to a user or group feed."""
        view = View.GROUP_FEED if message.user_type == "group" else View.USER_FEED
        self.state.navigate_to(view, target=message.username)
        menu = self.query_one(MenuBar)
        menu.set_view(view)
        await self.refresh_content()

    async def on_compose_block_post_requested(
        self, message: ComposeBlock.PostRequested
    ) -> None:
        """Handle post creation request."""
        try:
            await self.app.api.create_post(message.body, message.feeds)
            # Reset compose block
            compose = self.query_one(ComposeBlock)
            compose.reset()
            self.notify("Posted!")
            # Refresh feed to show new post
            await self.refresh_content()
        except Exception as e:
            self.show_error("Failed to post", e)

    async def on_comment_compose_comment_requested(
        self, message: CommentCompose.CommentRequested
    ) -> None:
        """Handle comment creation request."""
        try:
            comment = await self.app.api.create_comment(message.post_id, message.body)
            # Find the post block and add the comment
            for block in self.query(PostBlock):
                if block.post.id == message.post_id:
                    block.post.comments.append(comment)
                    block._hide_comment_compose()
                    block.refresh(recompose=True)
                    break
            self.notify("Comment added!")
        except Exception as e:
            self.show_error("Failed to add comment", e)

    async def on_post_block_edit_post_requested(
        self, message: PostBlock.EditPostRequested
    ) -> None:
        """Handle post edit request."""
        try:
            await self.app.api.update_post(message.post.id, message.new_body)
            # Update the post object
            message.post.body = message.new_body
            # Find and refresh the post block
            for block in self.query(PostBlock):
                if block.post.id == message.post.id:
                    block.editing_post = False
                    block.refresh(recompose=True)
                    break
            self.notify("Post updated!")
        except Exception as e:
            self.show_error("Failed to update post", e)

    async def on_post_block_delete_post_requested(
        self, message: PostBlock.DeletePostRequested
    ) -> None:
        """Handle post delete request."""
        try:
            await self.app.api.delete_post(message.post.id)
            # Find the post block and determine next focus target
            blocks = list(self.query(PostBlock))
            current_idx = None
            for idx, block in enumerate(blocks):
                if block.post.id == message.post.id:
                    current_idx = idx
                    block.remove()
                    break
            # Focus next post (or previous if last)
            if current_idx is not None and blocks:
                remaining = [b for b in blocks if b.post.id != message.post.id]
                if remaining:
                    if current_idx < len(remaining):
                        remaining[current_idx].focus()
                    else:
                        remaining[-1].focus()
            self.notify("Post deleted!")
        except Exception as e:
            self.show_error("Failed to delete post", e)

    async def on_post_block_edit_comment_requested(
        self, message: PostBlock.EditCommentRequested
    ) -> None:
        """Handle comment edit request."""
        try:
            await self.app.api.update_comment(message.comment.id, message.new_body)
            # Update the comment object
            message.comment.body = message.new_body
            # Find and refresh the post block containing the comment
            for block in self.query(PostBlock):
                for comment in block.post.comments:
                    if comment.id == message.comment.id:
                        # Reset editing state and recompose
                        for cb in block.query("CommentBlock"):
                            if hasattr(cb, "editing") and cb.editing:
                                cb.editing = False
                        block.refresh(recompose=True)
                        self.notify("Comment updated!")
                        return
        except Exception as e:
            self.show_error("Failed to update comment", e)

    async def on_post_block_delete_comment_requested(
        self, message: PostBlock.DeleteCommentRequested
    ) -> None:
        """Handle comment delete request."""
        try:
            await self.app.api.delete_comment(message.comment.id)
            # Find the post block containing the comment and remove it
            for block in self.query(PostBlock):
                for i, comment in enumerate(block.post.comments):
                    if comment.id == message.comment.id:
                        # Determine next focus target
                        next_focus_idx = min(i, len(block.post.comments) - 2)
                        block.post.comments.pop(i)
                        block.refresh(recompose=True)
                        # Focus next comment or post block
                        if next_focus_idx >= 0 and block.post.comments:
                            block.set_timer(
                                0.05,
                                lambda b=block, n=next_focus_idx: b.focus_comment_at(n),
                            )
                        else:
                            block.focus()
                        self.notify("Comment deleted!")
                        return
        except Exception as e:
            self.show_error("Failed to delete comment", e)
