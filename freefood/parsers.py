"""Parsers for FreeFeed API responses."""

from datetime import datetime

from httpx import URL

from freefood.models import Attachment, Comment, Notification, Post, User


class ResponseParser:
    """Parser for API responses."""

    def __init__(self, base_url: str) -> None:
        """Initialize parser."""
        self.base_url = base_url

    def parse_user(self, data: dict) -> User:
        """Parse user data from API response."""
        return User(
            id=data["id"],
            username=data["username"],
            screen_name=data.get("screenName", data["username"]),
            type=data.get("type", "user"),
            profile_picture_url=data.get("profilePictureMediumUrl"),
        )

    def parse_comment(
        self, data: dict, users_by_id: dict[str, User], current_user: User | None
    ) -> Comment:
        """Parse comment data from API response."""
        author = users_by_id.get(data["createdBy"])
        is_own = (
            author is not None
            and current_user is not None
            and author.id == current_user.id
        )
        return Comment(
            id=data["id"],
            body=data["body"],
            author=author,
            created_at=datetime.fromtimestamp(int(data["createdAt"]) / 1000),
            likes=data.get("likes", 0),
            is_liked=data.get("hasOwnLike", False),
            is_own=is_own,
        )

    def get_attachment_url(self, attachment_data: dict) -> str | None:
        """Constructs an attachment URL based on available data."""
        att_id = attachment_data.get("id")

        if not att_id:
            return None

        # Priority 1: Check if 'url' is directly provided (as per design spec)
        if attachment_data.get("url"):
            # Ensure base_url is also joined with the raw URL if it's relative
            return str(URL(self.base_url).join(attachment_data["url"]))

        # Priority 2: Use /v4/attachments/{id}/original?redirect= for direct download
        # Use httpx.URL for robust path joining
        base_url_obj = URL(self.base_url)
        constructed_path = f"/v4/attachments/{att_id}/original"
        final_url_obj = base_url_obj.join(constructed_path).copy_with(
            params={"redirect": ""}
        )

        constructed_url = str(final_url_obj)
        return constructed_url

    def denormalize_posts(self, data: dict, current_user: User | None) -> list[Post]:
        """Convert normalized API response to Post objects."""
        users_by_id = {u["id"]: self.parse_user(u) for u in data.get("users", [])}
        for group in data.get("groups", []):
            users_by_id[group["id"]] = self.parse_user(group)
        
        direct_subscriptions = {}
        for subscription in data.get("subscriptions", []):
            if subscription.get("name") == "Directs":
                user = users_by_id.get(subscription.get("user"))
                if user is not None:
                    direct_subscriptions[subscription.get("id")] = user
        
        comments_by_id = {
            c["id"]: self.parse_comment(c, users_by_id, current_user)
            for c in data.get("comments", [])
        }
        
        attachments_by_id = {}  # Initialize the dictionary
        for a in data.get("attachments", []):
            attachment_url = self.get_attachment_url(a)
            if not attachment_url:
                continue

            attachments_by_id[a["id"]] = Attachment(
                id=a["id"],
                file_name=a.get("fileName", ""),
                file_size=int(a.get("fileSize", 0)),
                media_type=a.get("mediaType", ""),
                url=attachment_url,
                thumbnail_url=a.get("thumbnailUrl"),
            )

        # Handle both list (timelines) and dict (single post) response formats
        posts_data = data.get("posts", [])
        if isinstance(posts_data, dict):
            posts_data = [posts_data]

        posts = []
        for p in posts_data:
            author = users_by_id.get(p["createdBy"])
            post_comments = [
                comments_by_id[cid]
                for cid in p.get("comments", [])
                if cid in comments_by_id
            ]
            post_likes = [
                users_by_id[uid] for uid in p.get("likes", []) if uid in users_by_id
            ]
            post_attachments = [
                attachments_by_id[aid]
                for aid in p.get("attachments", [])
                if aid in attachments_by_id
            ]
            groups = [
                users_by_id[fid]
                for fid in p.get("postedTo", [])
                if fid in users_by_id and users_by_id[fid].type == "group"
            ]
            direct_recipients = [
                direct_subscriptions[fid]
                for fid in p.get("postedTo", [])
                if fid in direct_subscriptions
            ]
            if author is not None:
                direct_recipients = [
                    recipient
                    for recipient in direct_recipients
                    if recipient.id != author.id
                ]
            is_own = (
                author is not None
                and current_user is not None
                and author.id == current_user.id
            )

            posts.append(
                Post(
                    id=p["id"],
                    body=p["body"],
                    author=author,
                    groups=groups,
                    created_at=datetime.fromtimestamp(int(p["createdAt"]) / 1000),
                    updated_at=datetime.fromtimestamp(int(p["updatedAt"]) / 1000),
                    comments=post_comments,
                    omitted_comments=p.get("omittedComments", 0),
                    omitted_comments_offset=p.get("omittedCommentsOffset", 0),
                    omitted_comment_likes=p.get("omittedCommentLikes", 0),
                    omitted_likes=p.get("omittedLikes", 0),
                    likes=post_likes,
                    attachments=post_attachments,
                    direct_recipients=direct_recipients,
                    is_liked=p.get("hasOwnLike", False),
                    is_hidden=p.get("isHidden", False),
                    is_own=is_own,
                )
            )
        return posts

    def parse_notifications(self, data: dict) -> list[Notification]:
        """Parse notifications from API response."""
        users_by_id = {u["id"]: self.parse_user(u) for u in data.get("users", [])}
        notifications = []
        for item in data.get("Notifications", []):
            created_user_id = item.get("created_user_id", item.get("createdBy"))
            created_user = users_by_id.get(created_user_id)
            if "date" in item:
                created_at = datetime.fromisoformat(item["date"].replace("Z", "+00:00"))
            else:
                created_at = datetime.fromtimestamp(
                    int(item.get("createdAt", "0")) / 1000
                )
            notifications.append(
                Notification(
                    id=item.get("id", ""),
                    event_id=item.get("eventId", item.get("event_id", "")),
                    event_type=item.get("eventType", item.get("event_type", "")),
                    date=created_at,
                    created_user=created_user,
                    post_id=item.get(
                        "postId", item.get("post_id", item.get("target_post_id"))
                    ),
                    comment_id=item.get(
                        "commentId",
                        item.get("comment_id", item.get("target_comment_id")),
                    ),
                )
            )
        return notifications
