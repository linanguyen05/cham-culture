"""End-to-end smoke test against a running server (http://127.0.0.1:8000).

Exercises the full frontend contract: register -> update_profile -> auth/me,
compat login, community feed/create/like/comment/share/stats/profile, guest
rejection, and static page serving. Prints PASS/FAIL per check.
"""

import io
import sys
import uuid

import httpx

BASE = "http://127.0.0.1:8000"

passed = 0
failed = 0


def check(name: str, ok: bool, extra: str = "") -> None:
    global passed, failed
    mark = "PASS" if ok else "FAIL"
    if ok:
        passed += 1
    else:
        failed += 1
    print(f"[{mark}] {name}" + (f" -- {extra}" if extra else ""))


PNG_1PX = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4"
    "890000000a49444154789c6360000002000154a24f6f0000000049454e44ae426082"
)


def main() -> int:
    origin = {"Origin": BASE}

    with httpx.Client(base_url=BASE, timeout=15.0, follow_redirects=False) as c:
        # Health
        r = c.get("/health")
        check("GET /health", r.status_code == 200 and r.json().get("status") == "ok", str(r.status_code))

        # Guest cannot access community
        r = c.get("/api/community/posts")
        check("guest GET /api/community/posts -> 401", r.status_code == 401, str(r.status_code))
        r = c.get("/api/auth/me")
        check("guest GET /api/auth/me -> 401", r.status_code == 401, str(r.status_code))

        # Register (unique email)
        email = f"tester_{uuid.uuid4().hex[:8]}@cham.vn"
        r = c.post("/register", json={"email": email, "password": "supersecret"}, headers=origin)
        ok = r.status_code == 200 and "userId" in r.json()
        check("POST /register", ok, str(r.status_code))
        user_id = r.json().get("userId") if ok else None

        # Duplicate register -> 409
        r = c.post("/register", json={"email": email, "password": "supersecret"}, headers=origin)
        check("POST /register duplicate -> 409", r.status_code == 409, str(r.status_code))

        # Short password rejected
        r = c.post("/register", json={"email": f"x_{uuid.uuid4().hex[:6]}@cham.vn", "password": "short"}, headers=origin)
        check("POST /register short pw -> 422", r.status_code == 422, str(r.status_code))

        # update_profile (multipart, userId from register, no session yet)
        files = {"avatar": ("a.png", io.BytesIO(PNG_1PX), "image/png")}
        data = {"username": "Người Kiểm Thử", "userId": user_id or ""}
        r = c.post("/update_profile", data=data, files=files, headers=origin)
        ok = r.status_code == 200 and r.json().get("user", {}).get("username") == "Người Kiểm Thử"
        avatar_url = r.json().get("user", {}).get("avatar_url") if r.status_code == 200 else None
        check("POST /update_profile", ok, str(r.status_code))
        # cookie set by update_profile -> authenticated now
        r = c.get("/api/auth/me")
        check("GET /api/auth/me after update_profile", r.status_code == 200 and r.json().get("authenticated"), str(r.status_code))

        # avatar served from /uploads
        if avatar_url:
            r = c.get(avatar_url)
            check("GET uploaded avatar", r.status_code == 200 and r.headers.get("content-type", "").startswith("image"), f"{r.status_code} {avatar_url}")

        # logout clears session
        r = c.post("/api/auth/logout", headers=origin)
        check("POST /api/auth/logout", r.status_code == 200, str(r.status_code))
        r = c.get("/api/auth/me")
        check("me after logout -> 401", r.status_code == 401, str(r.status_code))

        # Login unknown email -> 404
        r = c.post("/login", json={"email": "nobody@nowhere.vn", "password": "whatever12"}, headers=origin)
        check("POST /login unknown -> 404", r.status_code == 404, str(r.status_code))

        # Login demo user (seeded)
        r = c.post("/login", json={"email": "minhanh@gmail.com", "password": "123Aa"}, headers=origin)
        ok = r.status_code == 200 and r.json().get("user", {}).get("user_id")
        me_id = r.json().get("user", {}).get("user_id") if ok else None
        check("POST /login demo user", ok, str(r.status_code))

        # Wrong password -> 401
        r = c.post("/login", json={"email": "minhanh@gmail.com", "password": "wrongpass1"}, headers=origin)
        check("POST /login wrong pw -> 401", r.status_code == 401, str(r.status_code))

        # Re-login to restore session (previous wrong-pw call didn't drop it, but be safe)
        c.post("/login", json={"email": "minhanh@gmail.com", "password": "123Aa"}, headers=origin)

        # Feed (seeded)
        r = c.get("/api/community/posts?sort=latest&page=1&limit=20")
        ok = r.status_code == 200 and len(r.json().get("items", [])) >= 6
        check("GET /api/community/posts (seeded feed)", ok, f"{r.status_code} items={len(r.json().get('items', []))}")

        # popular sort + category filter
        r = c.get("/api/community/posts?sort=popular")
        check("GET posts sort=popular", r.status_code == 200, str(r.status_code))
        r = c.get("/api/community/posts?category=Lễ hội")
        check("GET posts category filter", r.status_code == 200, str(r.status_code))
        r = c.get("/api/community/posts?category=Invalid")
        check("GET posts invalid category -> 422", r.status_code == 422, str(r.status_code))

        # Create a post
        fd = {"content": "Bài viết kiểm thử tự động.", "category": "Daily"}
        r = c.post("/api/community/posts", data=fd, headers=origin)
        ok = r.status_code == 200 and r.json().get("id")
        post_id = r.json().get("id") if ok else None
        check("POST /api/community/posts", ok, str(r.status_code))

        # Create post with image
        files = [("images", ("p.png", PNG_1PX, "image/png"))]
        r = c.post("/api/community/posts", data={"content": "Có ảnh", "category": "Văn hóa Chăm"}, files=files, headers=origin)
        ok = r.status_code == 200
        img_post_id = r.json().get("id") if ok else None
        check("POST post with image", ok, str(r.status_code))
        # verify image url returned in feed
        r = c.get("/api/community/posts?category=Văn hóa Chăm")
        found = any(p["id"] == img_post_id and p.get("image_urls") for p in r.json().get("items", []))
        check("created post has image_urls", found)

        # Like toggle
        r = c.post(f"/api/community/posts/{post_id}/like", headers=origin)
        ok = r.status_code == 200 and r.json().get("liked") is True and r.json().get("like_count") == 1
        check("POST like (on)", ok, str(r.status_code))
        r = c.post(f"/api/community/posts/{post_id}/like", headers=origin)
        ok = r.status_code == 200 and r.json().get("liked") is False and r.json().get("like_count") == 0
        check("POST like (off)", ok, str(r.status_code))
        r = c.post("/api/community/posts/nonexistent/like", headers=origin)
        check("POST like missing post -> 404", r.status_code == 404, str(r.status_code))

        # Comment
        r = c.post(f"/api/community/posts/{post_id}/comments", json={"content": "Bình luận thử"}, headers=origin)
        ok = r.status_code == 200 and r.json().get("content") == "Bình luận thử"
        check("POST comment", ok, str(r.status_code))
        r = c.get(f"/api/community/posts/{post_id}/comments")
        ok = r.status_code == 200 and len(r.json().get("items", [])) == 1
        check("GET comments", ok, str(r.status_code))
        r = c.post(f"/api/community/posts/{post_id}/comments", json={"content": "   "}, headers=origin)
        check("POST empty comment -> 422", r.status_code == 422, str(r.status_code))

        # Share
        r = c.post(f"/api/community/posts/{post_id}/share", json={"content": "Chia sẻ thử"}, headers=origin)
        ok = r.status_code == 200 and r.json().get("id")
        share_id = r.json().get("id") if ok else None
        check("POST share", ok, str(r.status_code))
        # shared post should expose original_post in feed
        r = c.get("/api/community/posts?category=Daily")
        shared = next((p for p in r.json().get("items", []) if p["id"] == share_id), None)
        check("shared post has original_post", bool(shared and shared.get("original_post")))

        # Stats
        r = c.get("/api/community/stats/topics")
        check("GET stats/topics", r.status_code == 200 and len(r.json().get("items", [])) > 0, str(r.status_code))
        r = c.get("/api/community/stats/active-members")
        check("GET stats/active-members", r.status_code == 200 and len(r.json().get("items", [])) > 0, str(r.status_code))

        # Profile (own -> email present)
        r = c.get(f"/api/community/profiles/{me_id}")
        ok = r.status_code == 200 and r.json().get("is_current_user") and "email" in r.json().get("user", {})
        check("GET own profile (email present)", ok, str(r.status_code))
        # Profile of another seeded user -> no email
        others = c.get("/api/community/stats/active-members").json().get("items", [])
        other_id = next((m["user_id"] for m in others if m["user_id"] != me_id), None)
        if other_id:
            r = c.get(f"/api/community/profiles/{other_id}")
            ok = r.status_code == 200 and not r.json().get("is_current_user") and "email" not in r.json().get("user", {})
            check("GET other profile (email hidden)", ok, str(r.status_code))
        r = c.get("/api/community/profiles/doesnotexist")
        check("GET profile missing -> 404", r.status_code == 404, str(r.status_code))

        # CSRF / origin guard: POST with a foreign Origin should be blocked
        r = c.post("/api/community/posts/%s/like" % post_id, headers={"Origin": "http://evil.example"})
        check("cross-origin POST -> 403", r.status_code == 403, str(r.status_code))

        # Static pages
        for path, needle in [
            ("/", "Đăng nhập"),
            ("/index.html", "Đăng nhập"),
            ("/dashboard/index.html", "DÂN TỘC CHĂM"),
            ("/community/index.html", "community.js"),
            ("/community/community.js", "api/community"),
            ("/community/community.css", "style.css"),
            ("/profile.html", "profileForm"),
        ]:
            r = c.get(path)
            ok = r.status_code == 200 and needle in r.text
            check(f"GET {path}", ok, str(r.status_code))

    print(f"\n==== {passed} passed, {failed} failed ====")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
