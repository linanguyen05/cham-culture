from fastapi import Response

from app.config import get_settings
from app.middleware.auth import _decode_session, _encode_session, clear_session_cookie, set_session_cookie


def test_session_payload_is_encrypted_and_round_trips():
    settings = get_settings()
    payload = {"user_id": "abc", "issued_at": 1234567890}
    token = _encode_session(settings, payload)
    assert "abc" not in token
    assert _decode_session(settings, token) == payload


def test_session_cookie_is_httponly():
    settings = get_settings()
    response = Response()
    set_session_cookie(response, settings, {"user_id": "abc", "issued_at": 1234567890})
    header = response.headers["set-cookie"].lower()
    assert "httponly" in header
    assert settings.session_cookie_name.lower() in header


def test_clear_session_cookie():
    settings = get_settings()
    response = Response()
    clear_session_cookie(response, settings)
    assert "max-age=0" in response.headers["set-cookie"].lower()
