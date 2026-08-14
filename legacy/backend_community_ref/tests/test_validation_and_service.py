import io

import pytest
from fastapi import UploadFile
from pydantic import ValidationError

from app.community.schemas import CommentCreate, ShareCreate
from app.community.service import CommunityService
from app.config import get_settings


class FakeRepository:
    def __init__(self, share_post=None):
        self.share_post = share_post
        self.created = []

    async def create_post(self, **kwargs):
        self.created.append(kwargs)
        return "new-post-id"

    async def get_post_for_share(self, post_id):
        return self.share_post


class FakeStorage:
    def __init__(self):
        self.uploaded = []
        self.deleted = []

    async def upload_image(self, data, content_type, original_name):
        url = f"https://storage/{len(self.uploaded)}-{original_name}"
        self.uploaded.append((url, data, content_type))
        return url

    async def delete_image(self, url):
        self.deleted.append(url)


def upload_file(name: str, content_type: str, data: bytes) -> UploadFile:
    return UploadFile(filename=name, file=io.BytesIO(data), headers={"content-type": content_type})


@pytest.mark.asyncio
async def test_create_post_requires_content_or_image():
    service = CommunityService(FakeRepository(), FakeStorage(), get_settings())
    with pytest.raises(Exception) as exc:
        await service.create_post(user_id="u1", content=" ", category="Daily", files=[])
    assert getattr(exc.value, "status_code", None) == 422


@pytest.mark.asyncio
async def test_create_post_rejects_invalid_category():
    service = CommunityService(FakeRepository(), FakeStorage(), get_settings())
    with pytest.raises(Exception) as exc:
        await service.create_post(user_id="u1", content="hello", category="Invalid", files=[])
    assert getattr(exc.value, "status_code", None) == 422


@pytest.mark.asyncio
async def test_create_post_rejects_more_than_four_images():
    service = CommunityService(FakeRepository(), FakeStorage(), get_settings())
    files = [upload_file(f"{i}.png", "image/png", b"\x89PNG\r\n\x1a\n") for i in range(5)]
    with pytest.raises(Exception) as exc:
        await service.create_post(user_id="u1", content="hello", category="Daily", files=files)
    assert getattr(exc.value, "status_code", None) == 422


@pytest.mark.asyncio
async def test_create_post_uploads_images_and_serializes_urls_at_repository_boundary():
    repo = FakeRepository()
    storage = FakeStorage()
    service = CommunityService(repo, storage, get_settings())
    files = [
        upload_file("a.png", "image/png", b"\x89PNG\r\n\x1a\n"),
        upload_file("b.webp", "image/webp", b"RIFF0000WEBP"),
    ]
    post_id = await service.create_post(user_id="u1", content="hello", category="Daily", files=files)
    assert post_id == "new-post-id"
    assert len(storage.uploaded) == 2
    assert repo.created[0]["image_urls"] == [
        "https://storage/0-a.png",
        "https://storage/1-b.webp",
    ]


@pytest.mark.asyncio
async def test_create_post_cleans_uploaded_files_when_database_insert_fails():
    class FailingRepository(FakeRepository):
        async def create_post(self, **kwargs):
            raise RuntimeError("db failed")

    repo = FailingRepository()
    storage = FakeStorage()
    service = CommunityService(repo, storage, get_settings())
    with pytest.raises(Exception) as exc:
        await service.create_post(
            user_id="u1",
            content="hello",
            category="Daily",
            files=[upload_file("a.png", "image/png", b"\x89PNG\r\n\x1a\n")],
        )
    assert getattr(exc.value, "status_code", None) == 500
    assert storage.deleted == ["https://storage/0-a.png"]


@pytest.mark.asyncio
async def test_share_existing_post_inherits_category():
    repo = FakeRepository(share_post={"id": "original", "category": "Văn hóa Chăm"})
    service = CommunityService(repo, FakeStorage(), get_settings())
    new_id = await service.share_post(user_id="u2", post_id="original", content=" lời dẫn ")
    assert new_id == "new-post-id"
    assert repo.created[0]["shared_post_id"] == "original"
    assert repo.created[0]["category"] == "Văn hóa Chăm"
    assert repo.created[0]["content"] == "lời dẫn"


@pytest.mark.asyncio
async def test_share_missing_post_is_404():
    repo = FakeRepository(share_post=None)
    service = CommunityService(repo, FakeStorage(), get_settings())
    with pytest.raises(Exception) as exc:
        await service.share_post(user_id="u2", post_id="missing", content="")
    assert getattr(exc.value, "status_code", None) == 404


def test_empty_comment_is_rejected():
    with pytest.raises(ValidationError):
        CommentCreate(content="   ")


def test_share_content_can_be_empty():
    assert ShareCreate(content="  ").content == ""
