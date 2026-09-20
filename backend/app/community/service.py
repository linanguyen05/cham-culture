"""Business rules for posts, likes, comments, shares and community stats."""

from __future__ import annotations

from fastapi import HTTPException, UploadFile

from app.community.repository import CommunityRepository
from app.community.schemas import ALLOWED_CATEGORIES
from app.config import Settings
from app.storage.service import StorageService


class CommunityService:
    def __init__(
        self,
        repo: CommunityRepository,
        storage: StorageService,
        settings: Settings,
    ) -> None:
        self.repo = repo
        self.storage = storage
        self.settings = settings

    async def create_post(
        self,
        *,
        user_id: str,
        content: str,
        category: str,
        files: list[UploadFile],
        video: UploadFile | None = None,
    ) -> str:
        content = content.strip()
        category = category.strip()
        files = [f for f in files if f is not None and f.filename]
        has_video = video is not None and bool(video.filename)

        if not content and not files and not has_video:
            raise HTTPException(422, detail={"error": "VALIDATION_ERROR", "message": "Bài viết phải có nội dung, ảnh hoặc video."})
        if len(content) > self.settings.max_content_length:
            raise HTTPException(422, detail={"error": "VALIDATION_ERROR", "message": "Nội dung bài viết quá dài."})
            
        if not category:
            raise HTTPException(422, detail={"error": "CATEGORY_REQUIRED", "message": "Vui lòng chọn một chuyên mục cho bài viết."})
        if category not in ALLOWED_CATEGORIES:
            raise HTTPException(422, detail={"error": "VALIDATION_ERROR", "message": "Chủ đề không hợp lệ."})
            
        if len(files) > self.settings.max_upload_images:
            raise HTTPException(422, detail={"error": "VALIDATION_ERROR", "message": f"Chỉ được tải tối đa {self.settings.max_upload_images} ảnh."})

        uploaded_urls: list[str] = []
        video_url: str | None = None
        try:
            for file in files:
                data = await file.read()
                self._validate_image(file.content_type or "", data, file.filename or "")
                url = await self.storage.upload_image(
                    data, file.content_type or "", file.filename or "image"
                )
                uploaded_urls.append(url)

            if has_video and video:
                v_data = await video.read()
                self._validate_video(
                    video.content_type or "", v_data, video.filename or "video", self.settings.max_video_size_bytes
                )
                video_url = await self.storage.upload_video(
                    v_data, video.content_type or "video/mp4", video.filename or "video.mp4"
                )
                uploaded_urls.append(video_url)

            return await self.repo.create_post(
                user_id=user_id,
                content=content,
                category=category,
                image_urls=[u for u in uploaded_urls if u != video_url],
                video_url=video_url,
            )
        except HTTPException:
            await self._cleanup(uploaded_urls)
            raise
        except Exception as exc:
            await self._cleanup(uploaded_urls)
            raise HTTPException(
                status_code=500,
                detail={"error": "INTERNAL_SERVER_ERROR", "message": "Không thể tạo bài viết."},
            ) from exc

    async def add_comment(
        self,
        *,
        user_id: str,
        post_id: str,
        content: str,
        image: UploadFile | None = None,
        video: UploadFile | None = None,
    ) -> dict:
        content = content.strip()
        has_img = image is not None and bool(image.filename)
        has_vid = video is not None and bool(video.filename)

        if not content and not has_img and not has_vid:
            raise HTTPException(422, detail={"error": "VALIDATION_ERROR", "message": "Bình luận phải có nội dung, ảnh hoặc video."})
        if len(content) > self.settings.max_comment_length:
            raise HTTPException(422, detail={"error": "VALIDATION_ERROR", "message": "Nội dung bình luận quá dài."})

        uploaded_urls: list[str] = []
        image_url: str | None = None
        video_url: str | None = None

        try:
            if has_img and image:
                img_data = await image.read()
                self._validate_image(
                    image.content_type or "", img_data, image.filename or "image", self.settings.max_comment_media_size_bytes
                )
                image_url = await self.storage.upload_comment_media(
                    img_data, image.content_type or "image/png", image.filename or "image.png", is_video=False
                )
                uploaded_urls.append(image_url)

            if has_vid and video:
                vid_data = await video.read()
                self._validate_video(
                    video.content_type or "", vid_data, video.filename or "video", self.settings.max_comment_media_size_bytes
                )
                video_url = await self.storage.upload_comment_media(
                    vid_data, video.content_type or "video/mp4", video.filename or "video.mp4", is_video=True
                )
                uploaded_urls.append(video_url)

            return await self.repo.add_comment(
                user_id=user_id,
                post_id=post_id,
                content=content,
                image_url=image_url,
                video_url=video_url,
            )
        except HTTPException:
            await self._cleanup(uploaded_urls)
            raise
        except Exception as exc:
            await self._cleanup(uploaded_urls)
            raise HTTPException(
                status_code=500,
                detail={"error": "INTERNAL_SERVER_ERROR", "message": "Không thể thêm bình luận."},
            ) from exc

    async def share_post(self, *, user_id: str, post_id: str, content: str) -> str:
        original = await self.repo.get_post_for_share(post_id)
        if original is None:
            raise HTTPException(404, detail={"error": "NOT_FOUND", "message": "Bài viết gốc không tồn tại."})
        return await self.repo.create_post(
            user_id=user_id,
            content=content.strip(),
            category=original["category"],
            image_urls=[],
            shared_post_id=original["id"],
        )

    def _validate_image(self, content_type: str, data: bytes, filename: str, max_size: int | None = None) -> None:
        limit = max_size or self.settings.max_image_size_bytes
        allowed = {"image/jpeg", "image/png", "image/webp"}
        if content_type not in allowed:
            raise HTTPException(422, detail={"error": "VALIDATION_ERROR", "message": "Chỉ chấp nhận ảnh JPEG, PNG hoặc WebP."})
        if len(data) == 0 or len(data) > limit:
            raise HTTPException(422, detail={"error": "VALIDATION_ERROR", "message": f"Ảnh không hợp lệ hoặc vượt quá dung lượng cho phép ({limit // (1024*1024)}MB)."})
        if content_type == "image/jpeg" and not data.startswith(b"\xff\xd8\xff"):
            raise HTTPException(422, detail={"error": "VALIDATION_ERROR", "message": f"File {filename} không phải JPEG hợp lệ."})
        if content_type == "image/png" and data[:8] != b"\x89PNG\r\n\x1a\n":
            raise HTTPException(422, detail={"error": "VALIDATION_ERROR", "message": f"File {filename} không phải PNG hợp lệ."})
        if content_type == "image/webp" and not (data[:4] == b"RIFF" and data[8:12] == b"WEBP"):
            raise HTTPException(422, detail={"error": "VALIDATION_ERROR", "message": f"File {filename} không phải WebP hợp lệ."})

    def _validate_video(self, content_type: str, data: bytes, filename: str, max_size: int) -> None:
        allowed = {"video/mp4", "video/webm", "video/quicktime", "video/x-msvideo", "video/mpeg"}
        lower_name = filename.lower()
        valid_ext = any(lower_name.endswith(ext) for ext in [".mp4", ".webm", ".mov", ".avi"])
        if content_type not in allowed and not valid_ext:
            raise HTTPException(422, detail={"error": "VALIDATION_ERROR", "message": "Định dạng video không được hỗ trợ. Vui lòng chọn MP4, WebM hoặc MOV."})
        if len(data) == 0 or len(data) > max_size:
            raise HTTPException(422, detail={"error": "VALIDATION_ERROR", "message": f"Video vượt quá dung lượng cho phép ({max_size // (1024*1024)}MB)."})

    async def _cleanup(self, urls: list[str]) -> None:
        for url in urls:
            try:
                await self.storage.delete_image(url)
            except Exception:
                pass
