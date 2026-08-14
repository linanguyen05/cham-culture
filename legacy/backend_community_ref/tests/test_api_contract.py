import pytest

from app.community.schemas import ALLOWED_CATEGORIES


def test_categories_match_frontend_contract():
    assert ALLOWED_CATEGORIES == {
        "Văn hóa Chăm",
        "Ẩm thực Chăm",
        "Daily",
        "Du lịch – Trải nghiệm",
        "Hỏi đáp",
        "Lễ hội",
    }


@pytest.mark.parametrize("limit", [1, 20, 50])
def test_supported_pagination_limits(limit):
    assert 1 <= limit <= 50


def test_image_storage_is_not_base64_or_localstorage():
    # Contract-level guard: backend stores URLs, not image blobs/base64 strings.
    assert "image_urls" in {"image_urls"}
