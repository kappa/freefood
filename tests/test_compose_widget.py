"""Tests for ComposeBlock widget."""

import pytest
from textual.app import App


class TestComposeBlockInitialization:
    """Tests for ComposeBlock initialization."""

    def test_compose_block_exists(self):
        """ComposeBlock widget should be importable."""
        from freefood.widgets.compose import ComposeBlock

        widget = ComposeBlock()
        assert widget is not None

    def test_compose_block_starts_collapsed(self):
        """ComposeBlock should start in collapsed state."""
        from freefood.widgets.compose import ComposeBlock

        widget = ComposeBlock()
        assert widget.is_expanded is False


class TestComposeBlockCollapsedState:
    """Tests for ComposeBlock in collapsed state."""

    @pytest.mark.asyncio
    async def test_collapsed_shows_placeholder(self):
        """Collapsed state should show a placeholder input."""
        from freefood.widgets.compose import ComposeBlock
        from textual.widgets import Input

        class TestApp(App):
            def compose(self):
                yield ComposeBlock()

        async with TestApp().run_test() as pilot:
            app = pilot.app
            compose = app.query_one(ComposeBlock)

            # Should show a placeholder input
            placeholder = app.query_one("#compose-placeholder", Input)
            assert placeholder is not None
            assert placeholder.placeholder == "Write something..."

    @pytest.mark.asyncio
    async def test_typing_in_placeholder_expands_widget(self):
        """Typing in the placeholder should expand the widget."""
        from freefood.widgets.compose import ComposeBlock

        class TestApp(App):
            def compose(self):
                yield ComposeBlock()

        async with TestApp().run_test() as pilot:
            app = pilot.app
            compose = app.query_one(ComposeBlock)

            # Initially collapsed
            assert compose.is_expanded is False

            # Focus and type in the placeholder
            placeholder = app.query_one("#compose-placeholder")
            placeholder.focus()
            await pilot.press("h")
            await pilot.pause()

            # Should now be expanded
            assert compose.is_expanded is True

    @pytest.mark.asyncio
    async def test_enter_in_placeholder_expands_widget(self):
        """Pressing Enter in the placeholder should expand the widget."""
        from freefood.widgets.compose import ComposeBlock

        class TestApp(App):
            def compose(self):
                yield ComposeBlock()

        async with TestApp().run_test() as pilot:
            app = pilot.app
            compose = app.query_one(ComposeBlock)

            # Initially collapsed
            assert compose.is_expanded is False

            # Focus and press Enter
            placeholder = app.query_one("#compose-placeholder")
            placeholder.focus()
            await pilot.press("enter")
            await pilot.pause()

            # Should now be expanded
            assert compose.is_expanded is True

    @pytest.mark.asyncio
    async def test_textarea_focused_after_expansion(self):
        """TextArea should be focused after expansion."""
        from freefood.widgets.compose import ComposeBlock
        from textual.widgets import TextArea

        class TestApp(App):
            def compose(self):
                yield ComposeBlock()

        async with TestApp().run_test() as pilot:
            app = pilot.app
            compose = app.query_one(ComposeBlock)

            # Focus placeholder and press Enter to expand
            placeholder = app.query_one("#compose-placeholder")
            placeholder.focus()
            await pilot.press("enter")
            await pilot.pause()

            # TextArea should be focused
            textarea = app.query_one("#compose-body", TextArea)
            assert app.focused is textarea


class TestComposeBlockExpandedState:
    """Tests for ComposeBlock in expanded state."""

    @pytest.mark.asyncio
    async def test_expanded_shows_textarea(self):
        """Expanded state should show a TextArea for the body."""
        from freefood.widgets.compose import ComposeBlock
        from textual.widgets import TextArea

        class TestApp(App):
            def compose(self):
                yield ComposeBlock()

        async with TestApp().run_test() as pilot:
            app = pilot.app
            compose = app.query_one(ComposeBlock)

            # Expand the widget
            compose.is_expanded = True
            compose.refresh(recompose=True)
            await pilot.pause()

            # Should have a TextArea
            textarea = app.query_one("#compose-body", TextArea)
            assert textarea is not None

    @pytest.mark.asyncio
    async def test_expanded_shows_post_to_field(self):
        """Expanded state should show a 'Post to' input field."""
        from freefood.widgets.compose import ComposeBlock
        from textual.widgets import Input

        class TestApp(App):
            def compose(self):
                yield ComposeBlock()

        async with TestApp().run_test() as pilot:
            app = pilot.app
            compose = app.query_one(ComposeBlock)

            # Expand the widget
            compose.is_expanded = True
            compose.refresh(recompose=True)
            await pilot.pause()

            # Should have a "Post to" input
            post_to = app.query_one("#compose-post-to", Input)
            assert post_to is not None
            assert post_to.placeholder == "Post to..."

    @pytest.mark.asyncio
    async def test_expanded_shows_cancel_button(self):
        """Expanded state should show a Cancel button."""
        from freefood.widgets.compose import ComposeBlock
        from textual.widgets import Button

        class TestApp(App):
            def compose(self):
                yield ComposeBlock()

        async with TestApp().run_test() as pilot:
            app = pilot.app
            compose = app.query_one(ComposeBlock)

            # Expand the widget
            compose.is_expanded = True
            compose.refresh(recompose=True)
            await pilot.pause()

            # Should have a Cancel button
            cancel_btn = app.query_one("#compose-cancel", Button)
            assert cancel_btn is not None
            assert cancel_btn.label.plain == "Cancel"

    @pytest.mark.asyncio
    async def test_expanded_shows_post_button(self):
        """Expanded state should show a Post button."""
        from freefood.widgets.compose import ComposeBlock
        from textual.widgets import Button

        class TestApp(App):
            def compose(self):
                yield ComposeBlock()

        async with TestApp().run_test() as pilot:
            app = pilot.app
            compose = app.query_one(ComposeBlock)

            # Expand the widget
            compose.is_expanded = True
            compose.refresh(recompose=True)
            await pilot.pause()

            # Should have a Post button
            post_btn = app.query_one("#compose-post", Button)
            assert post_btn is not None
            assert post_btn.label.plain == "Post"


class TestComposeBlockCancelAction:
    """Tests for Cancel button behavior."""

    @pytest.mark.asyncio
    async def test_cancel_collapses_widget(self):
        """Clicking Cancel should collapse the widget."""
        from freefood.widgets.compose import ComposeBlock
        from textual.widgets import Button

        class TestApp(App):
            def compose(self):
                yield ComposeBlock()

        async with TestApp().run_test() as pilot:
            app = pilot.app
            compose = app.query_one(ComposeBlock)

            # Expand the widget
            compose.is_expanded = True
            compose.refresh(recompose=True)
            await pilot.pause()

            # Click Cancel
            cancel_btn = app.query_one("#compose-cancel", Button)
            cancel_btn.press()
            await pilot.pause()

            # Should be collapsed again
            assert compose.is_expanded is False


class TestComposeBlockPostAction:
    """Tests for Post button behavior."""

    def test_post_requested_message_exists(self):
        """PostRequested message should be defined."""
        from freefood.widgets.compose import ComposeBlock

        # The message class should exist
        assert hasattr(ComposeBlock, "PostRequested")

    @pytest.mark.asyncio
    async def test_post_button_emits_message_with_body(self):
        """Clicking Post should emit PostRequested with body and feeds."""
        from freefood.widgets.compose import ComposeBlock
        from textual.widgets import Button, TextArea

        messages_received = []

        class TestApp(App):
            def compose(self):
                yield ComposeBlock()

            def on_compose_block_post_requested(self, event):
                messages_received.append(event)

        async with TestApp().run_test() as pilot:
            app = pilot.app
            compose = app.query_one(ComposeBlock)

            # Expand and type a message
            compose.is_expanded = True
            compose.refresh(recompose=True)
            await pilot.pause()

            textarea = app.query_one("#compose-body", TextArea)
            textarea.text = "Hello world"
            await pilot.pause()

            # Click Post
            post_btn = app.query_one("#compose-post", Button)
            post_btn.press()
            await pilot.pause()

            # Should have emitted a message
            assert len(messages_received) == 1
            assert messages_received[0].body == "Hello world"

    @pytest.mark.asyncio
    async def test_post_button_includes_feeds(self):
        """PostRequested should include feeds from the 'Post to' field."""
        from freefood.widgets.compose import ComposeBlock
        from textual.widgets import Button, TextArea, Input

        messages_received = []

        class TestApp(App):
            def compose(self):
                yield ComposeBlock()

            def on_compose_block_post_requested(self, event):
                messages_received.append(event)

        async with TestApp().run_test() as pilot:
            app = pilot.app
            compose = app.query_one(ComposeBlock)

            # Expand and set up message
            compose.is_expanded = True
            compose.refresh(recompose=True)
            await pilot.pause()

            textarea = app.query_one("#compose-body", TextArea)
            textarea.text = "Test post"

            post_to = app.query_one("#compose-post-to", Input)
            post_to.value = "news, updates"
            await pilot.pause()

            # Click Post
            post_btn = app.query_one("#compose-post", Button)
            post_btn.press()
            await pilot.pause()

            # Should include the feeds
            assert len(messages_received) == 1
            assert messages_received[0].feeds == ["news", "updates"]

    @pytest.mark.asyncio
    async def test_empty_body_does_not_post(self):
        """Empty body should not emit PostRequested."""
        from freefood.widgets.compose import ComposeBlock
        from textual.widgets import Button

        messages_received = []

        class TestApp(App):
            def compose(self):
                yield ComposeBlock()

            def on_compose_block_post_requested(self, event):
                messages_received.append(event)

        async with TestApp().run_test() as pilot:
            app = pilot.app
            compose = app.query_one(ComposeBlock)

            # Expand but leave body empty
            compose.is_expanded = True
            compose.refresh(recompose=True)
            await pilot.pause()

            # Click Post with empty body
            post_btn = app.query_one("#compose-post", Button)
            post_btn.press()
            await pilot.pause()

            # Should NOT have emitted a message
            assert len(messages_received) == 0


class TestComposeBlockKeyboard:
    """Tests for keyboard navigation."""

    @pytest.mark.asyncio
    async def test_escape_collapses_expanded_widget(self):
        """Pressing Escape should collapse the expanded widget."""
        from freefood.widgets.compose import ComposeBlock

        class TestApp(App):
            def compose(self):
                yield ComposeBlock()

        async with TestApp().run_test() as pilot:
            app = pilot.app
            compose = app.query_one(ComposeBlock)

            # Expand the widget
            compose.is_expanded = True
            compose.refresh(recompose=True)
            await pilot.pause()

            # Focus something in the compose block
            compose.focus()
            await pilot.press("escape")
            await pilot.pause()

            # Should be collapsed
            assert compose.is_expanded is False


class TestComposeBlockReset:
    """Tests for reset method."""

    @pytest.mark.asyncio
    async def test_reset_collapses_and_clears(self):
        """reset() should collapse and clear the widget."""
        from freefood.widgets.compose import ComposeBlock
        from textual.widgets import TextArea, Input

        class TestApp(App):
            def compose(self):
                yield ComposeBlock()

        async with TestApp().run_test() as pilot:
            app = pilot.app
            compose = app.query_one(ComposeBlock)

            # Expand and add content
            compose.is_expanded = True
            compose.refresh(recompose=True)
            await pilot.pause()

            textarea = app.query_one("#compose-body", TextArea)
            textarea.text = "Test message"
            post_to = app.query_one("#compose-post-to", Input)
            post_to.value = "news"
            await pilot.pause()

            # Reset
            compose.reset()
            await pilot.pause()

            # Should be collapsed
            assert compose.is_expanded is False
