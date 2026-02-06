"""Tests for edit functionality."""

import pytest
from textual.app import App, ComposeResult
from textual.widgets import Button, TextArea

from freefood.models import Comment, User
from freefood.widgets.post import PostBlock
from tests.test_post_widget import make_post


class TestEditPostButton:
    """Tests for Edit button on posts."""

    @pytest.fixture
    def own_post(self):
        return make_post(id="post-123", body="Original post body", is_own=True)

    @pytest.fixture
    def other_post(self):
        return make_post(id="post-456", body="Someone else's post", is_own=False)

    async def test_edit_button_shown_for_own_post(self, own_post):
        """Edit button is visible for own posts."""

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield PostBlock(own_post)

        async with TestApp().run_test() as pilot:
            post_block = pilot.app.query_one(PostBlock)
            post_block.focus()
            await pilot.press("enter")  # Enter post mode
            edit_btn = pilot.app.query("#btn-edit")
            assert len(edit_btn) == 1

    async def test_edit_button_not_shown_for_other_post(self, other_post):
        """Edit button is not visible for other's posts."""

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield PostBlock(other_post)

        async with TestApp().run_test() as pilot:
            post_block = pilot.app.query_one(PostBlock)
            post_block.focus()
            await pilot.press("enter")  # Enter post mode
            edit_btn = pilot.app.query("#btn-edit")
            assert len(edit_btn) == 0


class TestEditPostMode:
    """Tests for post editing mode."""

    @pytest.fixture
    def own_post(self):
        return make_post(id="post-123", body="Original post body", is_own=True)

    async def test_edit_button_shows_textarea(self, own_post):
        """Clicking Edit shows TextArea with current body."""

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield PostBlock(own_post)

        async with TestApp().run_test() as pilot:
            post_block = pilot.app.query_one(PostBlock)
            post_block.focus()
            await pilot.press("enter")  # Enter post mode
            edit_btn = pilot.app.query_one("#btn-edit", Button)
            await pilot.click(edit_btn)
            # Should show textarea with original body
            textarea = pilot.app.query_one("#edit-post-body", TextArea)
            assert textarea.text == "Original post body"

    async def test_edit_mode_shows_save_cancel_buttons(self, own_post):
        """Edit mode shows Save and Cancel buttons."""

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield PostBlock(own_post)

        async with TestApp().run_test() as pilot:
            post_block = pilot.app.query_one(PostBlock)
            post_block.focus()
            await pilot.press("enter")
            edit_btn = pilot.app.query_one("#btn-edit", Button)
            await pilot.click(edit_btn)
            # Should show Save and Cancel buttons
            save_btn = pilot.app.query("#btn-save-edit")
            cancel_btn = pilot.app.query("#btn-cancel-edit")
            assert len(save_btn) == 1
            assert len(cancel_btn) == 1

    async def test_cancel_exits_edit_mode(self, own_post):
        """Cancel button exits edit mode without saving."""

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield PostBlock(own_post)

        async with TestApp().run_test() as pilot:
            post_block = pilot.app.query_one(PostBlock)
            post_block.focus()
            await pilot.press("enter")
            edit_btn = pilot.app.query_one("#btn-edit", Button)
            await pilot.click(edit_btn)
            # Modify text
            textarea = pilot.app.query_one("#edit-post-body", TextArea)
            textarea.clear()
            textarea.insert("Modified text")
            # Cancel
            cancel_btn = pilot.app.query_one("#btn-cancel-edit", Button)
            await pilot.click(cancel_btn)
            await pilot.pause()
            # Should exit edit mode and show original body
            assert len(pilot.app.query("#edit-post-body")) == 0
            assert post_block.post.body == "Original post body"

    async def test_save_emits_edit_requested_message(self, own_post):
        """Save button emits EditPostRequested with new body."""
        messages = []

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield PostBlock(own_post)

            def on_post_block_edit_post_requested(self, message):
                messages.append(message)

        async with TestApp().run_test() as pilot:
            post_block = pilot.app.query_one(PostBlock)
            post_block.focus()
            await pilot.press("enter")
            edit_btn = pilot.app.query_one("#btn-edit", Button)
            await pilot.click(edit_btn)
            # Modify text
            textarea = pilot.app.query_one("#edit-post-body", TextArea)
            textarea.clear()
            textarea.insert("Updated post body")
            # Save
            save_btn = pilot.app.query_one("#btn-save-edit", Button)
            await pilot.click(save_btn)
            await pilot.pause()
            # Should emit message with new body
            assert len(messages) == 1
            assert messages[0].new_body == "Updated post body"
            assert messages[0].post.id == "post-123"

    async def test_escape_cancels_edit_mode(self, own_post):
        """Escape key cancels edit mode."""

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield PostBlock(own_post)

        async with TestApp().run_test() as pilot:
            post_block = pilot.app.query_one(PostBlock)
            post_block.focus()
            await pilot.press("enter")
            edit_btn = pilot.app.query_one("#btn-edit", Button)
            await pilot.click(edit_btn)
            # Should be in edit mode
            assert len(pilot.app.query("#edit-post-body")) == 1
            # Press Escape
            await pilot.press("escape")
            await pilot.pause()
            # Should exit edit mode
            assert len(pilot.app.query("#edit-post-body")) == 0

    async def test_ctrl_enter_saves_edit(self, own_post):
        """Ctrl+Enter saves edit."""
        messages = []

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield PostBlock(own_post)

            def on_post_block_edit_post_requested(self, message):
                messages.append(message)

        async with TestApp().run_test() as pilot:
            post_block = pilot.app.query_one(PostBlock)
            post_block.focus()
            await pilot.press("enter")
            edit_btn = pilot.app.query_one("#btn-edit", Button)
            await pilot.click(edit_btn)
            # Modify text
            textarea = pilot.app.query_one("#edit-post-body", TextArea)
            textarea.clear()
            textarea.insert("Saved with shortcut")
            # Press Ctrl+Enter
            await pilot.press("ctrl+enter")
            await pilot.pause()
            # Should emit message
            assert len(messages) == 1
            assert messages[0].new_body == "Saved with shortcut"


class TestEditComment:
    """Tests for comment editing."""

    @pytest.fixture
    def own_comment(self):
        return Comment(
            id="comment-123",
            body="Original comment",
            author=User(id="u1", username="me", screen_name="Me", type="user"),
            created_at="1700000000000",
            likes=0,
            is_own=True,
        )

    @pytest.fixture
    def other_comment(self):
        return Comment(
            id="comment-456",
            body="Someone else's comment",
            author=User(id="u2", username="other", screen_name="Other", type="user"),
            created_at="1700000000000",
            likes=0,
            is_own=False,
        )

    @pytest.fixture
    def post_with_own_comment(self, own_comment):
        return make_post(id="post-123", body="Post body", comments=[own_comment])

    @pytest.fixture
    def post_with_other_comment(self, other_comment):
        return make_post(id="post-456", body="Post body", comments=[other_comment])

    async def test_edit_button_shown_on_own_comment(self, post_with_own_comment):
        """Edit button shows on own comments."""

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield PostBlock(post_with_own_comment)

        async with TestApp().run_test() as pilot:
            post_block = pilot.app.query_one(PostBlock)
            post_block.focus()
            await pilot.press("enter")  # Enter post mode
            edit_btns = pilot.app.query(".comment-edit-btn")
            assert len(edit_btns) == 1

    async def test_edit_button_not_shown_on_other_comment(
        self, post_with_other_comment
    ):
        """Edit button not shown on other's comments."""

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield PostBlock(post_with_other_comment)

        async with TestApp().run_test() as pilot:
            post_block = pilot.app.query_one(PostBlock)
            post_block.focus()
            await pilot.press("enter")  # Enter post mode
            edit_btns = pilot.app.query(".comment-edit-btn")
            assert len(edit_btns) == 0


class TestEditCommentMode:
    """Tests for comment editing mode."""

    @pytest.fixture
    def own_comment(self):
        return Comment(
            id="comment-123",
            body="Original comment",
            author=User(id="u1", username="me", screen_name="Me", type="user"),
            created_at="1700000000000",
            likes=0,
            is_own=True,
        )

    @pytest.fixture
    def post_with_own_comment(self, own_comment):
        return make_post(id="post-123", body="Post body", comments=[own_comment])

    async def test_edit_comment_shows_textarea(self, post_with_own_comment):
        """Clicking Edit on comment shows TextArea with current body."""

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield PostBlock(post_with_own_comment)

        async with TestApp().run_test() as pilot:
            post_block = pilot.app.query_one(PostBlock)
            post_block.focus()
            await pilot.press("enter")  # Enter post mode
            edit_btn = pilot.app.query_one(".comment-edit-btn", Button)
            await pilot.click(edit_btn)
            await pilot.pause()
            # Should show textarea with original body
            textarea = pilot.app.query_one("#edit-comment-body", TextArea)
            assert textarea.text == "Original comment"

    async def test_edit_comment_shows_save_cancel_buttons(self, post_with_own_comment):
        """Edit comment mode shows Save and Cancel buttons."""

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield PostBlock(post_with_own_comment)

        async with TestApp().run_test() as pilot:
            post_block = pilot.app.query_one(PostBlock)
            post_block.focus()
            await pilot.press("enter")
            edit_btn = pilot.app.query_one(".comment-edit-btn", Button)
            await pilot.click(edit_btn)
            await pilot.pause()
            save_btn = pilot.app.query("#btn-save-comment-edit")
            cancel_btn = pilot.app.query("#btn-cancel-comment-edit")
            assert len(save_btn) == 1
            assert len(cancel_btn) == 1

    async def test_cancel_comment_edit_exits_mode(self, post_with_own_comment):
        """Cancel exits comment edit mode."""

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield PostBlock(post_with_own_comment)

        async with TestApp().run_test() as pilot:
            post_block = pilot.app.query_one(PostBlock)
            post_block.focus()
            await pilot.press("enter")
            edit_btn = pilot.app.query_one(".comment-edit-btn", Button)
            await pilot.click(edit_btn)
            await pilot.pause()
            cancel_btn = pilot.app.query_one("#btn-cancel-comment-edit", Button)
            cancel_btn.press()
            await pilot.pause()
            # Should exit edit mode
            assert len(pilot.app.query("#edit-comment-body")) == 0

    async def test_save_comment_emits_message(self, post_with_own_comment):
        """Save button emits EditCommentRequested with new body."""
        messages = []

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield PostBlock(post_with_own_comment)

            def on_post_block_edit_comment_requested(self, message):
                messages.append(message)

        async with TestApp().run_test() as pilot:
            post_block = pilot.app.query_one(PostBlock)
            post_block.focus()
            await pilot.press("enter")
            edit_btn = pilot.app.query_one(".comment-edit-btn", Button)
            await pilot.click(edit_btn)
            await pilot.pause()
            # Modify text
            textarea = pilot.app.query_one("#edit-comment-body", TextArea)
            textarea.clear()
            textarea.insert("Updated comment")
            # Save
            save_btn = pilot.app.query_one("#btn-save-comment-edit", Button)
            save_btn.press()
            await pilot.pause()
            # Should emit message with new body
            assert len(messages) == 1
            assert messages[0].new_body == "Updated comment"
            assert messages[0].comment.id == "comment-123"

    async def test_escape_cancels_comment_edit(self, post_with_own_comment):
        """Escape key cancels comment edit mode."""

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield PostBlock(post_with_own_comment)

        async with TestApp().run_test() as pilot:
            post_block = pilot.app.query_one(PostBlock)
            post_block.focus()
            await pilot.press("enter")
            edit_btn = pilot.app.query_one(".comment-edit-btn", Button)
            await pilot.click(edit_btn)
            await pilot.pause()
            # Should be in edit mode
            assert len(pilot.app.query("#edit-comment-body")) == 1
            # Press Escape
            await pilot.press("escape")
            await pilot.pause()
            # Should exit edit mode
            assert len(pilot.app.query("#edit-comment-body")) == 0

    async def test_ctrl_enter_saves_comment_edit(self, post_with_own_comment):
        """Ctrl+Enter saves comment edit."""
        messages = []

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield PostBlock(post_with_own_comment)

            def on_post_block_edit_comment_requested(self, message):
                messages.append(message)

        async with TestApp().run_test() as pilot:
            post_block = pilot.app.query_one(PostBlock)
            post_block.focus()
            await pilot.press("enter")
            edit_btn = pilot.app.query_one(".comment-edit-btn", Button)
            await pilot.click(edit_btn)
            await pilot.pause()
            # Modify text
            textarea = pilot.app.query_one("#edit-comment-body", TextArea)
            textarea.clear()
            textarea.insert("Saved with shortcut")
            # Press Ctrl+Enter
            await pilot.press("ctrl+enter")
            await pilot.pause()
            # Should emit message
            assert len(messages) == 1
            assert messages[0].new_body == "Saved with shortcut"


class TestDeletePostButton:
    """Tests for Delete button on posts."""

    @pytest.fixture
    def own_post(self):
        return make_post(id="post-123", body="My post", is_own=True)

    @pytest.fixture
    def other_post(self):
        return make_post(id="post-456", body="Other post", is_own=False)

    async def test_delete_button_shown_for_own_post(self, own_post):
        """Delete button is visible for own posts."""

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield PostBlock(own_post)

        async with TestApp().run_test() as pilot:
            post_block = pilot.app.query_one(PostBlock)
            post_block.focus()
            await pilot.press("enter")
            delete_btn = pilot.app.query("#btn-delete")
            assert len(delete_btn) == 1

    async def test_delete_button_not_shown_for_other_post(self, other_post):
        """Delete button is not visible for other's posts."""

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield PostBlock(other_post)

        async with TestApp().run_test() as pilot:
            post_block = pilot.app.query_one(PostBlock)
            post_block.focus()
            await pilot.press("enter")
            delete_btn = pilot.app.query("#btn-delete")
            assert len(delete_btn) == 0

    async def test_delete_button_shows_confirmation(self, own_post):
        """Clicking Delete shows confirmation buttons."""

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield PostBlock(own_post)

        async with TestApp().run_test() as pilot:
            post_block = pilot.app.query_one(PostBlock)
            post_block.focus()
            await pilot.press("enter")
            delete_btn = pilot.app.query_one("#btn-delete", Button)
            await pilot.click(delete_btn)
            # Should show confirmation
            confirm_btn = pilot.app.query("#btn-confirm-delete")
            cancel_btn = pilot.app.query("#btn-cancel-delete")
            assert len(confirm_btn) == 1
            assert len(cancel_btn) == 1

    async def test_cancel_delete_hides_confirmation(self, own_post):
        """Cancelling delete hides confirmation."""

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield PostBlock(own_post)

        async with TestApp().run_test() as pilot:
            post_block = pilot.app.query_one(PostBlock)
            post_block.focus()
            await pilot.press("enter")
            delete_btn = pilot.app.query_one("#btn-delete", Button)
            await pilot.click(delete_btn)
            # Cancel
            cancel_btn = pilot.app.query_one("#btn-cancel-delete", Button)
            await pilot.click(cancel_btn)
            await pilot.pause()
            # Should hide confirmation and show normal delete button
            assert len(pilot.app.query("#btn-confirm-delete")) == 0
            assert len(pilot.app.query("#btn-delete")) == 1

    async def test_confirm_delete_emits_message(self, own_post):
        """Confirming delete emits DeletePostRequested."""
        messages = []

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield PostBlock(own_post)

            def on_post_block_delete_post_requested(self, message):
                messages.append(message)

        async with TestApp().run_test() as pilot:
            post_block = pilot.app.query_one(PostBlock)
            post_block.focus()
            await pilot.press("enter")
            delete_btn = pilot.app.query_one("#btn-delete", Button)
            await pilot.click(delete_btn)
            # Confirm
            confirm_btn = pilot.app.query_one("#btn-confirm-delete", Button)
            await pilot.click(confirm_btn)
            await pilot.pause()
            # Should emit message
            assert len(messages) == 1
            assert messages[0].post.id == "post-123"


class TestDeleteComment:
    """Tests for comment deletion."""

    @pytest.fixture
    def own_comment(self):
        return Comment(
            id="comment-123",
            body="My comment",
            author=User(id="u1", username="me", screen_name="Me", type="user"),
            created_at="1700000000000",
            likes=0,
            is_own=True,
        )

    @pytest.fixture
    def other_comment(self):
        return Comment(
            id="comment-456",
            body="Other comment",
            author=User(id="u2", username="other", screen_name="Other", type="user"),
            created_at="1700000000000",
            likes=0,
            is_own=False,
        )

    @pytest.fixture
    def post_with_own_comment(self, own_comment):
        return make_post(id="post-123", body="Post body", comments=[own_comment])

    @pytest.fixture
    def post_with_other_comment(self, other_comment):
        return make_post(id="post-456", body="Post body", comments=[other_comment])

    async def test_delete_button_shown_on_own_comment(self, post_with_own_comment):
        """Delete button shows on own comments."""

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield PostBlock(post_with_own_comment)

        async with TestApp().run_test() as pilot:
            post_block = pilot.app.query_one(PostBlock)
            post_block.focus()
            await pilot.press("enter")  # Enter post mode
            delete_btns = pilot.app.query(".comment-delete-btn")
            assert len(delete_btns) == 1

    async def test_delete_button_not_shown_on_other_comment(
        self, post_with_other_comment
    ):
        """Delete button not shown on other's comments."""

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield PostBlock(post_with_other_comment)

        async with TestApp().run_test() as pilot:
            post_block = pilot.app.query_one(PostBlock)
            post_block.focus()
            await pilot.press("enter")  # Enter post mode
            delete_btns = pilot.app.query(".comment-delete-btn")
            assert len(delete_btns) == 0

    async def test_delete_comment_shows_confirmation(self, post_with_own_comment):
        """Clicking Delete on comment shows confirmation buttons."""

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield PostBlock(post_with_own_comment)

        async with TestApp().run_test() as pilot:
            post_block = pilot.app.query_one(PostBlock)
            post_block.focus()
            await pilot.press("enter")
            delete_btn = pilot.app.query_one(".comment-delete-btn", Button)
            await pilot.click(delete_btn)
            await pilot.pause()
            # Should show confirmation buttons
            confirm_btn = pilot.app.query(".comment-confirm-delete-btn")
            cancel_btn = pilot.app.query(".comment-cancel-delete-btn")
            assert len(confirm_btn) == 1
            assert len(cancel_btn) == 1

    async def test_confirm_delete_comment_emits_message(self, post_with_own_comment):
        """Confirming delete emits DeleteCommentRequested."""
        messages = []

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield PostBlock(post_with_own_comment)

            def on_post_block_delete_comment_requested(self, message):
                messages.append(message)

        async with TestApp().run_test() as pilot:
            post_block = pilot.app.query_one(PostBlock)
            post_block.focus()
            await pilot.press("enter")
            delete_btn = pilot.app.query_one(".comment-delete-btn", Button)
            await pilot.click(delete_btn)
            await pilot.pause()
            confirm_btn = pilot.app.query_one(".comment-confirm-delete-btn", Button)
            confirm_btn.press()
            await pilot.pause()
            assert len(messages) == 1
            assert messages[0].comment.id == "comment-123"
