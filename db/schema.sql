-- ===========================================================================
-- gacha_gacha スキーマ定義
--
-- 学習用に「正規化された 5 テーブル + セッション 1 テーブル」で構成。
-- 各 CREATE TABLE の前に "なぜこの形なのか" を日本語コメントで書いています。
-- ===========================================================================

-- ---------------------------------------------------------------------------
-- users: ログインアカウント
-- ---------------------------------------------------------------------------
-- name はログインID。display_name は画面表示用。
-- パスワードは平文で持たない。pbkdf2_hmac でハッシュ化したものを格納する。
-- ハッシュアルゴリズム + イテレーション回数 + ソルト + ダイジェストを
-- "$" 区切りで 1 カラムに詰めている (passlib 形式の簡易版)。
-- coins はガチャを回すための仮想通貨 (初期 1000)。
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id           BIGSERIAL    PRIMARY KEY,
    name         TEXT         NOT NULL UNIQUE,
    pass_hash    TEXT         NOT NULL,
    display_name TEXT         NOT NULL,
    coins        INTEGER      NOT NULL DEFAULT 1000,
    created_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- ---------------------------------------------------------------------------
-- characters: ガチャから出るキャラ (もしくはアイテム)
-- ---------------------------------------------------------------------------
-- rarity は 1..5 の整数。クライアントで星の数として表示する。
-- emoji は雰囲気づくり。画像URLでも構わない。
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS characters (
    id      BIGSERIAL PRIMARY KEY,
    name    TEXT      NOT NULL UNIQUE,
    rarity  SMALLINT  NOT NULL CHECK (rarity BETWEEN 1 AND 5),
    emoji   TEXT      NOT NULL DEFAULT '❓'
);

-- ---------------------------------------------------------------------------
-- gachas: ガチャ筐体 (どのガチャを引くか)
-- ---------------------------------------------------------------------------
-- 同時に複数の "ガチャ" を運用できるようにテーブル化している。
-- price は 1 回引くのに必要な coins。
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS gachas (
    id    BIGSERIAL PRIMARY KEY,
    name  TEXT      NOT NULL UNIQUE,
    price INTEGER   NOT NULL CHECK (price > 0)
);

-- ---------------------------------------------------------------------------
-- gacha_items: 「どのガチャから、どのキャラが、どのくらいの確率で出るか」
-- ---------------------------------------------------------------------------
-- (gacha_id, character_id) の組み合わせは 1 行。
-- 確率は weight で表す。実確率は SUM(weight) との比で決まる。
-- これにより
--   ・後から weight を変えるだけで確率調整できる
--   ・ガチャごとに排出キャラを完全に分離できる
-- というメリットがある。
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS gacha_items (
    id           BIGSERIAL PRIMARY KEY,
    gacha_id     BIGINT    NOT NULL REFERENCES gachas(id)     ON DELETE CASCADE,
    character_id BIGINT    NOT NULL REFERENCES characters(id) ON DELETE RESTRICT,
    weight       INTEGER   NOT NULL CHECK (weight > 0),
    UNIQUE (gacha_id, character_id)
);

CREATE INDEX IF NOT EXISTS idx_gacha_items_gacha ON gacha_items(gacha_id);

-- ---------------------------------------------------------------------------
-- user_characters: ユーザー所持品 (= Box)
-- ---------------------------------------------------------------------------
-- ガチャを 1 回引くごとに 1 行 INSERT される (重複OK = 同じキャラが何枚でも出る)
-- 「所持しているか」は EXISTS / COUNT で問い合わせる。
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS user_characters (
    id           BIGSERIAL   PRIMARY KEY,
    user_id      BIGINT      NOT NULL REFERENCES users(id)      ON DELETE CASCADE,
    character_id BIGINT      NOT NULL REFERENCES characters(id) ON DELETE RESTRICT,
    obtained_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_user_characters_user ON user_characters(user_id);
CREATE INDEX IF NOT EXISTS idx_user_characters_user_char
    ON user_characters(user_id, character_id);

-- ---------------------------------------------------------------------------
-- sessions: クッキーで持つセッショントークン
-- ---------------------------------------------------------------------------
-- 学習用なので「DB に置く」最も素直な形にしている。
-- token は十分に長いランダム文字列 (256bit base64url) を入れる。
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sessions (
    token      TEXT        PRIMARY KEY,
    user_id    BIGINT      NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);
