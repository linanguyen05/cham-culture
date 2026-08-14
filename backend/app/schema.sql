-- Cham Culture Community — local SQLite schema.
-- Uses TEXT UUID ids to preserve the string-id contract of the original
-- Supabase/Postgres design. Timestamps are stored as ISO-8601 UTC strings.

CREATE TABLE IF NOT EXISTS users (
    id            TEXT PRIMARY KEY,
    username      TEXT,
    email         TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    avatar_url    TEXT,
    created_at    TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE TABLE IF NOT EXISTS posts (
    id             TEXT PRIMARY KEY,
    created_at     TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    content        TEXT NOT NULL DEFAULT '',
    image_url      TEXT NOT NULL DEFAULT '',
    user_id        TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category       TEXT NOT NULL DEFAULT 'Daily',
    shared_post_id TEXT REFERENCES posts(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS comments (
    id         TEXT PRIMARY KEY,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    content    TEXT NOT NULL,
    user_id    TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    post_id    TEXT NOT NULL REFERENCES posts(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS post_likes (
    post_id TEXT NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    PRIMARY KEY (post_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_posts_created  ON posts(created_at DESC, id DESC);
CREATE INDEX IF NOT EXISTS idx_posts_category ON posts(category);
CREATE INDEX IF NOT EXISTS idx_posts_user     ON posts(user_id);
CREATE INDEX IF NOT EXISTS idx_comments_post  ON comments(post_id);
CREATE INDEX IF NOT EXISTS idx_likes_post     ON post_likes(post_id);
