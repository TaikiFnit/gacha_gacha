-- ============================================================================
-- ch02 / step 1 — まず users テーブルだけ作って、SELECT/INSERT/UPDATE する。
-- ============================================================================
-- 使い方 (Postgres を docker compose で起動済み前提):
--   docker compose exec db psql -U gacha -d gacha
--   gacha=> \i /docker-entrypoint-initdb.d/...   ← 注意: 本番DBは既にseed済みなので
--                                                   このファイルは「別DBで試す」のがおすすめ
--
-- 練習用に "playground" DB を作って、そっちで実験するパターン:
--   gacha=> CREATE DATABASE play;
--   gacha=> \c play
--   play=>  \i exercises/ch02/step1_users_only.sql   (←ホストから読み込み)
--
-- もしくはホスト側から:
--   docker compose exec -T db psql -U gacha -d play < exercises/ch02/step1_users_only.sql
-- ============================================================================

DROP TABLE IF EXISTS users;

CREATE TABLE users (
    id          BIGSERIAL    PRIMARY KEY,                  -- 自動採番
    name        TEXT         NOT NULL UNIQUE,              -- 重複不可
    pass_hash   TEXT         NOT NULL,
    coins       INTEGER      NOT NULL DEFAULT 1000 CHECK (coins >= 0),
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- INSERT 3 件
INSERT INTO users (name, pass_hash) VALUES
    ('alice', 'fake_hash_1'),
    ('bob',   'fake_hash_2'),
    ('carol', 'fake_hash_3');

-- SELECT
SELECT id, name, coins, created_at FROM users ORDER BY id;

-- UPDATE: alice にコインを 500 おまけ
UPDATE users SET coins = coins + 500 WHERE name = 'alice'
RETURNING id, name, coins;

-- ----------------------------------------------------------------------------
-- 演習 (このSQLは実行せず psql で自分で打って実験する)
-- ----------------------------------------------------------------------------
-- (a) name が重複したらどうなるか:
--     INSERT INTO users (name, pass_hash) VALUES ('alice', 'x');
--   → 何というエラーが出るか観察 (UNIQUE 制約が効いている)
--
-- (b) coins を負にできるか:
--     UPDATE users SET coins = -1 WHERE name = 'bob';
--   → CHECK 制約に殴られる
--
-- (c) created_at を入れずに INSERT すると、何が入るか確認
--     INSERT INTO users (name, pass_hash) VALUES ('dave', 'h');
--     SELECT name, created_at FROM users WHERE name='dave';
