from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

# The frontend (unmodifiable) uses these category labels, but the Supabase
# `posts.category` CHECK constraint allows a different, shorter set. We map
# between them: frontend label -> DB value on write/filter, DB value -> frontend
# label on read. Labels that are identical in both need no translation.
CATEGORY_TO_DB = {
    "Văn hóa Chăm": "Văn hóa",
    "Ẩm thực Chăm": "Ẩm thưc",
    "Hỏi đáp": "Câu hỏi",
    "Du lịch – Trải nghiệm": "Trải nghiệm",
    "Lễ hội": "Lễ hội",
    "Daily": "Daily",
}
CATEGORY_FROM_DB = {db: fe for fe, db in CATEGORY_TO_DB.items()}

# API-facing (frontend) categories accepted by the endpoints.
ALLOWED_CATEGORIES = set(CATEGORY_TO_DB)


def to_db_category(value: str) -> str:
    return CATEGORY_TO_DB.get(value, value)


def from_db_category(value: str) -> str:
    return CATEGORY_FROM_DB.get(value, value)


class AuthorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    username: str
    avatar_url: str | None = None


class OriginalPostOut(BaseModel):
    id: str
    created_at: datetime
    content: str
    image_urls: list[str] = Field(default_factory=list)
    author: AuthorOut


class PostOut(BaseModel):
    id: str
    created_at: datetime
    content: str
    image_urls: list[str] = Field(default_factory=list)
    category: str
    shared_post_id: str | None = None
    author: AuthorOut
    like_count: int
    comment_count: int
    liked_by_current_user: bool
    original_post: OriginalPostOut | None = None


class PaginationOut(BaseModel):
    page: int
    limit: int
    has_next: bool


class PostsResponse(BaseModel):
    items: list[PostOut]
    pagination: PaginationOut


class CommentUserOut(BaseModel):
    id: str
    username: str
    avatar_url: str | None = None


class CommentOut(BaseModel):
    id: str
    created_at: datetime
    content: str
    user: CommentUserOut


class CommentsResponse(BaseModel):
    items: list[CommentOut]


class CommentCreate(BaseModel):
    content: str = Field(min_length=1, max_length=1000)

    @field_validator("content")
    @classmethod
    def strip_content(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Nội dung bình luận không được để trống.")
        return value


class ShareCreate(BaseModel):
    content: str = Field(default="", max_length=2000)

    @field_validator("content")
    @classmethod
    def strip_content(cls, value: str) -> str:
        return value.strip()


class TopicStatOut(BaseModel):
    category: str
    post_count: int


class TopicStatsResponse(BaseModel):
    items: list[TopicStatOut]


class ActiveMemberOut(BaseModel):
    user_id: str
    username: str
    avatar_url: str | None = None
    post_count: int


class ActiveMembersResponse(BaseModel):
    items: list[ActiveMemberOut]
