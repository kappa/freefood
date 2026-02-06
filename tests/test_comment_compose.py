"""Tests for CommentCompose widget."""

import pytest
from textual.app import App, ComposeResult
from textual.widgets import Button, TextArea

from freefood.widgets.comment_compose import CommentCompose
from freefood.widgets.post import PostBlock
from tests.test_post_widget import make_post


class TestCommentComposeInitialization:
    """Tests for CommentCompose widget initialization."""

    @pytest.fixture
    def post_id(self):
        return "test-post-123"

    def test_comment_compose_exists(self, post_id):
        """CommentCompose widget can be instantiated."""
        compose = CommentCompose(post_id=post_id)
        assert compose is not None
        assert compose.post_id == post_id


class TestCommentComposeUI:
    """Tests for CommentCompose UI elements."""

    @pytest.fixture
    def post_id(self):
        return "test-post-123"

    async def test_shows_textarea(self, post_id):
        """CommentCompose shows a TextArea for writing."""

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield CommentCompose(post_id=post_id)

        async with TestApp().run_test() as pilot:
            textarea = pilot.app.query_one(TextArea)
            assert textarea is not None

    async def test_shows_cancel_button(self, post_id):
        """CommentCompose shows a Cancel button."""

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield CommentCompose(post_id=post_id)

        async with TestApp().run_test() as pilot:
            cancel_btn = pilot.app.query_one("#comment-cancel", Button)
            assert cancel_btn is not None

    async def test_shows_submit_button(self, post_id):
        """CommentCompose shows a Submit button."""

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield CommentCompose(post_id=post_id)

        async with TestApp().run_test() as pilot:
            submit_btn = pilot.app.query_one("#comment-submit", Button)
            assert submit_btn is not None


class TestCommentComposeActions:
    """Tests for CommentCompose actions."""

    @pytest.fixture
    def post_id(self):
        return "test-post-123"

    async def test_cancel_emits_cancelled_message(self, post_id):
        """Cancel button emits CommentCancelled message."""
        messages = []

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield CommentCompose(post_id=post_id)

            def on_comment_compose_cancelled(self, message):
                messages.append(message)

        async with TestApp().run_test() as pilot:
            cancel_btn = pilot.app.query_one("#comment-cancel", Button)
            await pilot.click(cancel_btn)
            assert len(messages) == 1

    async def test_submit_emits_comment_requested_message(self, post_id):
        """Submit button emits CommentRequested message with body and post_id."""
        messages = []

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield CommentCompose(post_id=post_id)

            def on_comment_compose_comment_requested(self, message):
                messages.append(message)

        async with TestApp().run_test() as pilot:
            textarea = pilot.app.query_one("#comment-body", TextArea)
            textarea.insert("Test comment body")
            submit_btn = pilot.app.query_one("#comment-submit", Button)
            await pilot.click(submit_btn)
            assert len(messages) == 1
            assert messages[0].body == "Test comment body"
            assert messages[0].post_id == post_id

    async def test_empty_body_does_not_submit(self, post_id):
        """Empty comment body does not emit message."""
        messages = []

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield CommentCompose(post_id=post_id)

            def on_comment_compose_comment_requested(self, message):
                messages.append(message)

        async with TestApp().run_test() as pilot:
            submit_btn = pilot.app.query_one("#comment-submit", Button)
            await pilot.click(submit_btn)
            assert len(messages) == 0

    async def test_escape_cancels(self, post_id):
        """Escape key emits Cancelled message."""
        messages = []

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield CommentCompose(post_id=post_id)

            def on_comment_compose_cancelled(self, message):
                messages.append(message)

        async with TestApp().run_test() as pilot:
            compose = pilot.app.query_one(CommentCompose)
            compose.focus()
            await pilot.press("escape")
            assert len(messages) == 1

    async def test_ctrl_enter_submits(self, post_id):
        """Ctrl+Enter submits comment."""
        messages = []

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield CommentCompose(post_id=post_id)

            def on_comment_compose_comment_requested(self, message):
                messages.append(message)

        async with TestApp().run_test() as pilot:
            textarea = pilot.app.query_one("#comment-body", TextArea)
            textarea.insert("Test via Ctrl+Enter")
            compose = pilot.app.query_one(CommentCompose)
            compose.focus()
            await pilot.press("ctrl+enter")
            assert len(messages) == 1
            assert messages[0].body == "Test via Ctrl+Enter"


class TestCommentComposeIntegration:
    """Tests for CommentCompose integration with PostBlock."""

    @pytest.fixture
    def sample_post(self):
        return make_post(id="post-123", body="Test post")

    async def test_comment_button_shows_compose(self, sample_post):
        """Clicking Comment button shows CommentCompose widget."""

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield PostBlock(sample_post)

        async with TestApp().run_test() as pilot:
            post_block = pilot.app.query_one(PostBlock)
            # Enter post mode
            post_block.focus()
            await pilot.press("enter")
            # Click comment button
            comment_btn = pilot.app.query_one("#btn-comment", Button)
            await pilot.click(comment_btn)
            # CommentCompose should now be visible
            compose = pilot.app.query_one(CommentCompose)
            assert compose is not None
            assert compose.post_id == sample_post.id

    async def test_cancel_hides_compose(self, sample_post):
        """Cancelling hides CommentCompose widget."""

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield PostBlock(sample_post)

        async with TestApp().run_test() as pilot:
            post_block = pilot.app.query_one(PostBlock)
            post_block.focus()
            await pilot.press("enter")
            comment_btn = pilot.app.query_one("#btn-comment", Button)
            await pilot.click(comment_btn)
            # Verify compose is shown
            assert len(pilot.app.query(CommentCompose)) == 1
            # Press escape to cancel (more reliable than button click)
            compose = pilot.app.query_one(CommentCompose)
            compose.focus()
            await pilot.press("escape")
            await pilot.pause()
            # CommentCompose should be gone (PostBlock handles it)
            composes = pilot.app.query(CommentCompose)
            assert len(composes) == 0

    async def test_submit_hides_compose_and_adds_comment(self, sample_post):
        """Submitting comment hides compose and adds comment to post."""

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield PostBlock(sample_post)

            def on_comment_compose_comment_requested(self, message):
                # Simulate what FeedScreen would do - add comment to post
                for block in self.query(PostBlock):
                    if block.post.id == message.post_id:
                        from freefood.models import Comment, User

                        new_comment = Comment(
                            id="new-comment",
                            body=message.body,
                            author=User(
                                id="u1", username="me", screen_name="Me", type="user"
                            ),
                            created_at="1700000000000",
                            likes=0,
                        )
                        block.post.comments.append(new_comment)
                        # Hide compose and refresh
                        block._hide_comment_compose()
                        block.refresh(recompose=True)

        async with TestApp().run_test() as pilot:
            post_block = pilot.app.query_one(PostBlock)
            post_block.focus()
            await pilot.press("enter")
            comment_btn = pilot.app.query_one("#btn-comment", Button)
            await pilot.click(comment_btn)
            # Type comment
            textarea = pilot.app.query_one("#comment-body", TextArea)
            textarea.insert("My new comment")
            # Submit with Ctrl+Enter
            compose = pilot.app.query_one(CommentCompose)
            compose.focus()
            await pilot.press("ctrl+enter")
            await pilot.pause()
            # Comment compose should be gone
            assert len(pilot.app.query(CommentCompose)) == 0
            # Post should have the new comment
            assert len(post_block.post.comments) == 1
            assert post_block.post.comments[0].body == "My new comment"
