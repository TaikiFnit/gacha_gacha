-- ============================================================================
-- 0001_initial.sql — 最初のマイグレーション。 学習用の最小スキーマ。
-- ============================================================================
-- 本物の db/init.sql は触らないので、 ここでは練習用の小さなスキーマを切る。
-- ============================================================================

CREATE TABLE IF NOT EXISTS users (
    id          BIGSERIAL    PRIMARY KEY,
    name        TEXT         NOT NULL UNIQUE,
    pass_hash   TEXT         NOT NULL,
    coins       INTEGER      NOT NULL DEFAULT 1000 CHECK (coins >= 0),
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

INSERT INTO users (name, pass_hash) VALUES
    ('alice', 'fake_hash_1'),
    ('bob',   'fake_hash_2')
ON CONFLICT DO NOTHING;
