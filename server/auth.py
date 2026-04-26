"""認証まわり (パスワードハッシュ + セッショントークン)。

学習目的のため、外部依存に頼らず Python 標準ライブラリだけで実装している。

- パスワードハッシュ: hashlib.pbkdf2_hmac (sha256, 200_000 回)
  本番では argon2 や bcrypt を使うのが望ましい。学習用としては
  「ソルトを 1 ユーザーごとに作る」「ハッシュにアルゴリズム情報を埋め込む」
  という考え方を体感するのが目的。

- セッション: 32 byte の暗号学的乱数を base64url にして DB に保存する。
  クライアントには Set-Cookie で返す。
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

import psycopg

# pbkdf2 のパラメータ。学習しやすいよう小さめだが、200_000 はそこそこ実用的。
_PBKDF2_ALGO = "sha256"
_PBKDF2_ITER = 200_000
_PBKDF2_SALT_BYTES = 16
_PBKDF2_DKLEN = 32

# セッションの有効期間
SESSION_TTL = timedelta(days=7)


# ---------------------------------------------------------------------------
# パスワード
# ---------------------------------------------------------------------------
def hash_password(password: str) -> str:
    """パスワードをハッシュ化して、保存用文字列を返す。

    返り値の形式:
        pbkdf2_sha256$<iter>$<salt_b64>$<hash_b64>
    こうしておくとアルゴリズムや反復回数をあとから上げたいときに、
    既存ハッシュと共存しながら段階移行できる。
    """
    salt = os.urandom(_PBKDF2_SALT_BYTES)
    dk = hashlib.pbkdf2_hmac(_PBKDF2_ALGO, password.encode("utf-8"),
                             salt, _PBKDF2_ITER, dklen=_PBKDF2_DKLEN)
    return "$".join([
        f"pbkdf2_{_PBKDF2_ALGO}",
        str(_PBKDF2_ITER),
        base64.b64encode(salt).decode(),
        base64.b64encode(dk).decode(),
    ])


def verify_password(password: str, stored: str) -> bool:
    """保存されたハッシュ文字列と入力パスワードを比較する。"""
    try:
        algo, iter_s, salt_b64, hash_b64 = stored.split("$")
    except ValueError:
        return False
    if not algo.startswith("pbkdf2_"):
        return False
    digest_name = algo.split("_", 1)[1]
    iters = int(iter_s)
    salt = base64.b64decode(salt_b64)
    expected = base64.b64decode(hash_b64)
    actual = hashlib.pbkdf2_hmac(digest_name, password.encode("utf-8"),
                                 salt, iters, dklen=len(expected))
    # タイミング攻撃に強い比較。
    return hmac.compare_digest(actual, expected)


# ---------------------------------------------------------------------------
# セッション
# ---------------------------------------------------------------------------
def new_session_token() -> str:
    """十分に長いランダムトークンを生成する (256bit, URL-safe)。"""
    return secrets.token_urlsafe(32)


def create_session(conn: psycopg.Connection, user_id: int) -> tuple[str, datetime]:
    """sessions テーブルにレコードを差し込み、(token, expires_at) を返す。"""
    token = new_session_token()
    expires_at = datetime.now(timezone.utc) + SESSION_TTL
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO sessions (token, user_id, expires_at) VALUES (%s, %s, %s)",
            (token, user_id, expires_at),
        )
    return token, expires_at


def lookup_session(conn: psycopg.Connection, token: str) -> Optional[dict]:
    """token から user 情報を引く。期限切れは None を返す + 自動削除。"""
    if not token:
        return None
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT u.id, u.name, u.display_name, u.coins, s.expires_at
              FROM sessions s
              JOIN users    u ON u.id = s.user_id
             WHERE s.token = %s
            """,
            (token,),
        )
        row = cur.fetchone()
    if row is None:
        return None
    if row["expires_at"] <= datetime.now(timezone.utc):
        delete_session(conn, token)
        return None
    return {
        "id": row["id"],
        "name": row["name"],
        "display_name": row["display_name"],
        "coins": row["coins"],
    }


def delete_session(conn: psycopg.Connection, token: str) -> None:
    with conn.cursor() as cur:
        cur.execute("DELETE FROM sessions WHERE token = %s", (token,))
