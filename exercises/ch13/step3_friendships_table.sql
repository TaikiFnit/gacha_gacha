-- ============================================================================
-- ch13 / step 3 — friendships テーブル (方向あり + ステート + 自己ループ禁止)。
-- ============================================================================

DROP TABLE IF EXISTS friendships;

CREATE TABLE friendships (
    requester_id BIGINT      NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    addressee_id BIGINT      NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status       TEXT        NOT NULL CHECK (status IN ('pending', 'accepted', 'blocked')),
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (requester_id, addressee_id),
    CHECK (requester_id <> addressee_id)
);

CREATE INDEX idx_friend_addressee ON friendships(addressee_id, status);

-- ----------------------------------------------------------------------------
-- 動作確認
-- ----------------------------------------------------------------------------
-- (a) 自分にフレンド申請しようとすると CHECK 違反:
--   INSERT INTO friendships VALUES (1, 1, 'pending');   -- ← エラー
--
-- (b) 申請 → 承認 → 一覧
--   INSERT INTO friendships (requester_id, addressee_id, status) VALUES (1, 2, 'pending');
--   UPDATE friendships SET status = 'accepted' WHERE requester_id = 1 AND addressee_id = 2;
--
-- (c) 自分のフレンド一覧 (双方向に出す):
--   SELECT CASE WHEN requester_id = 1 THEN addressee_id ELSE requester_id END AS friend_id,
--          status, created_at
--     FROM friendships
--    WHERE (requester_id = 1 OR addressee_id = 1)
--      AND status = 'accepted';
