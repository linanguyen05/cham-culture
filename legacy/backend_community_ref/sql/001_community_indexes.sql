-- Optional performance migration. No schema columns/tables are changed.
CREATE INDEX IF NOT EXISTS idx_posts_created_at_id
    ON posts (created_at DESC, id DESC);

CREATE INDEX IF NOT EXISTS idx_posts_category_created_at_id
    ON posts (category, created_at DESC, id DESC);

CREATE INDEX IF NOT EXISTS idx_posts_user_id
    ON posts (user_id);

CREATE INDEX IF NOT EXISTS idx_posts_shared_post_id
    ON posts (shared_post_id);

CREATE INDEX IF NOT EXISTS idx_comments_post_id_created_at_id
    ON comments (post_id, created_at ASC, id ASC);

CREATE INDEX IF NOT EXISTS idx_comments_user_id
    ON comments (user_id);

-- post_likes already has a composite PK (post_id, user_id), which is enough
-- for the feed count/join and per-post duplicate prevention used here.
