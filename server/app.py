"""http.server だけで書かれたガチャ API。

なぜフレームワークを使わないのか:
  Flask や FastAPI を使うと「リクエストが来てから JSON を返すまで」の途中が
  全部隠されてしまう。学習目的では、HTTP メソッド + パス + ヘッダ + ボディが
  どう Python のオブジェクトに変換され、何をもって 200 / 400 / 401 を返すのか、
  全部目に見える状態にしておきたい。

エンドポイント:
  POST /api/register
  POST /api/login
  POST /api/logout              (要認証)
  GET  /api/me                  (要認証)
  GET  /api/gacha/list
  POST /api/gacha/pull          (要認証)
  GET  /api/box                 (要認証)

使い方:
  $ python -m server.app
  → http://localhost:8000 で待ち受け開始
"""

from __future__ import annotations

import http.cookies
import json
import os
import sys
import traceback
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Callable
from urllib.parse import urlparse

from . import auth, gacha
from .db import get_conn, healthcheck

# ---------------------------------------------------------------------------
# 設定
# ---------------------------------------------------------------------------
APP_PORT = int(os.getenv("APP_PORT", "8000"))

# CORS: 開発時にフロントを別ポート (例: 5500) で配信できるよう、
# 学習用としてゆるめに開けてある。本番ではきっちり絞る。
ALLOWED_ORIGINS = {
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    f"http://localhost:{APP_PORT}",
    f"http://127.0.0.1:{APP_PORT}",
}

SESSION_COOKIE = "gg_session"


# ---------------------------------------------------------------------------
# 例外クラス
# ---------------------------------------------------------------------------
class AppError(Exception):
    """アプリケーション層で投げる、HTTPステータス付きのエラー。"""

    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status
        self.message = message


def bad_request(msg: str) -> AppError: return AppError(400, msg)
def unauthorized(msg: str = "ログインが必要です") -> AppError: return AppError(401, msg)
def not_found(msg: str = "見つかりません") -> AppError: return AppError(404, msg)


# ---------------------------------------------------------------------------
# ルーター: (method, path) -> handler
# ---------------------------------------------------------------------------
Handler = Callable[["GachaHandler"], Any]
ROUTES: dict[tuple[str, str], Handler] = {}


def route(method: str, path: str):
    def deco(fn: Handler) -> Handler:
        ROUTES[(method.upper(), path)] = fn
        return fn
    return deco


# ---------------------------------------------------------------------------
# リクエストハンドラ
# ---------------------------------------------------------------------------
class GachaHandler(BaseHTTPRequestHandler):
    # 既定のログをカスタマイズ (見やすく)
    def log_message(self, fmt: str, *args: Any) -> None:
        sys.stderr.write(f"[{self.command}] {self.path} -> {fmt % args}\n")

    # ---------- レスポンス補助 ----------
    def _cors_headers(self) -> None:
        origin = self.headers.get("Origin", "")
        if origin in ALLOWED_ORIGINS:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Access-Control-Allow-Credentials", "true")
            self.send_header("Vary", "Origin")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def send_json(self, status: int, payload: Any,
                  set_cookie: http.cookies.SimpleCookie | None = None) -> None:
        body = json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8")
        self.send_response(status)
        self._cors_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        if set_cookie is not None:
            for morsel in set_cookie.values():
                self.send_header("Set-Cookie", morsel.OutputString())
        self.end_headers()
        self.wfile.write(body)

    # ---------- リクエスト解析 ----------
    def read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        if length == 0:
            return {}
        raw = self.rfile.read(length)
        try:
            data = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError as e:
            raise bad_request(f"JSON が読めません: {e}")
        if not isinstance(data, dict):
            raise bad_request("JSON の最上位はオブジェクトにしてください")
        return data

    def get_cookie(self, name: str) -> str:
        raw = self.headers.get("Cookie", "")
        if not raw:
            return ""
        jar = http.cookies.SimpleCookie()
        jar.load(raw)
        morsel = jar.get(name)
        return morsel.value if morsel else ""

    def require_user(self, conn) -> dict:
        token = self.get_cookie(SESSION_COOKIE)
        user = auth.lookup_session(conn, token)
        if user is None:
            raise unauthorized()
        return user

    # ---------- ディスパッチ ----------
    def do_OPTIONS(self) -> None:  # noqa: N802 - http.server convention
        self.send_response(HTTPStatus.NO_CONTENT)
        self._cors_headers()
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        self._dispatch("GET")

    def do_POST(self) -> None:  # noqa: N802
        self._dispatch("POST")

    def _dispatch(self, method: str) -> None:
        path = urlparse(self.path).path
        handler = ROUTES.get((method, path))
        if handler is None:
            self.send_json(404, {"error": "Not Found", "path": path})
            return
        try:
            handler(self)
        except AppError as e:
            self.send_json(e.status, {"error": e.message})
        except Exception as e:  # noqa: BLE001
            traceback.print_exc()
            self.send_json(500, {"error": "internal server error", "detail": str(e)})


# ---------------------------------------------------------------------------
# 共通: ユーザー情報を JSON 用に整える
# ---------------------------------------------------------------------------
def _user_payload(u: dict) -> dict:
    return {
        "id": u["id"],
        "name": u["name"],
        "display_name": u["display_name"],
        "coins": u["coins"],
    }


def _make_session_cookie(token: str) -> http.cookies.SimpleCookie:
    jar = http.cookies.SimpleCookie()
    jar[SESSION_COOKIE] = token
    m = jar[SESSION_COOKIE]
    m["path"] = "/"
    m["httponly"] = True
    m["samesite"] = "Lax"
    m["max-age"] = int(auth.SESSION_TTL.total_seconds())
    return jar


def _clear_session_cookie() -> http.cookies.SimpleCookie:
    jar = http.cookies.SimpleCookie()
    jar[SESSION_COOKIE] = ""
    m = jar[SESSION_COOKIE]
    m["path"] = "/"
    m["httponly"] = True
    m["samesite"] = "Lax"
    m["max-age"] = 0
    return jar


# ===========================================================================
# ルート定義
# ===========================================================================
@route("POST", "/api/register")
def register(h: GachaHandler) -> None:
    body = h.read_json()
    name = (body.get("name") or "").strip()
    password = body.get("password") or ""
    display_name = (body.get("display_name") or "").strip() or name
    if len(name) < 3 or len(name) > 32:
        raise bad_request("name は 3〜32 文字")
    if len(password) < 6:
        raise bad_request("password は 6 文字以上")

    pass_hash = auth.hash_password(password)
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM users WHERE name = %s", (name,))
            if cur.fetchone():
                raise bad_request("その name は既に使われています")
            cur.execute(
                """
                INSERT INTO users (name, pass_hash, display_name)
                VALUES (%s, %s, %s)
                RETURNING id, name, display_name, coins
                """,
                (name, pass_hash, display_name),
            )
            user = cur.fetchone()
        token, _ = auth.create_session(conn, user["id"])

    h.send_json(200, {"user": _user_payload(user)},
                set_cookie=_make_session_cookie(token))


@route("POST", "/api/login")
def login(h: GachaHandler) -> None:
    body = h.read_json()
    name = (body.get("name") or "").strip()
    password = body.get("password") or ""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, name, pass_hash, display_name, coins "
                "FROM users WHERE name = %s",
                (name,),
            )
            user = cur.fetchone()
        if user is None or not auth.verify_password(password, user["pass_hash"]):
            raise AppError(401, "name か password が違います")
        token, _ = auth.create_session(conn, user["id"])

    h.send_json(200, {"user": _user_payload(user)},
                set_cookie=_make_session_cookie(token))


@route("POST", "/api/logout")
def logout(h: GachaHandler) -> None:
    token = h.get_cookie(SESSION_COOKIE)
    if token:
        with get_conn() as conn:
            auth.delete_session(conn, token)
    h.send_json(200, {"ok": True}, set_cookie=_clear_session_cookie())


@route("GET", "/api/me")
def me(h: GachaHandler) -> None:
    with get_conn() as conn:
        user = h.require_user(conn)
    h.send_json(200, {"user": user})


@route("GET", "/api/gacha/list")
def gacha_list(h: GachaHandler) -> None:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT g.id, g.name, g.price,
                   COUNT(gi.id)        AS pool_size,
                   COALESCE(SUM(gi.weight), 0) AS total_weight
              FROM gachas g
              LEFT JOIN gacha_items gi ON gi.gacha_id = g.id
             GROUP BY g.id
             ORDER BY g.id
            """
        )
        rows = cur.fetchall()
    h.send_json(200, {"gachas": rows})


@route("POST", "/api/gacha/pull")
def gacha_pull(h: GachaHandler) -> None:
    body = h.read_json()
    gacha_id = body.get("gacha_id")
    if not isinstance(gacha_id, int):
        raise bad_request("gacha_id は整数で指定してください")

    with get_conn() as conn:
        user = h.require_user(conn)

        # 1. ガチャを取得 + 価格チェック (FOR UPDATE で行ロック)
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, name, price FROM gachas WHERE id = %s FOR SHARE",
                (gacha_id,),
            )
            g = cur.fetchone()
            if g is None:
                raise not_found("そのガチャは存在しません")

            cur.execute(
                "SELECT coins FROM users WHERE id = %s FOR UPDATE",
                (user["id"],),
            )
            row = cur.fetchone()
            coins = row["coins"]
            if coins < g["price"]:
                raise bad_request(
                    f"コインが足りません (必要 {g['price']} / 所持 {coins})"
                )

        # 2. 抽選
        pool = gacha.fetch_pool(conn, gacha_id)
        if not pool:
            raise bad_request("そのガチャには排出設定がありません")
        won = gacha.draw(pool)

        # 3. coins を引き、user_characters に INSERT
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET coins = coins - %s WHERE id = %s "
                "RETURNING coins",
                (g["price"], user["id"]),
            )
            new_coins = cur.fetchone()["coins"]

            cur.execute(
                "INSERT INTO user_characters (user_id, character_id) "
                "VALUES (%s, %s) RETURNING obtained_at",
                (user["id"], won.character_id),
            )
            obtained_at = cur.fetchone()["obtained_at"]

    h.send_json(200, {
        "gacha": {"id": g["id"], "name": g["name"], "price": g["price"]},
        "character": {
            "id": won.character_id,
            "name": won.name,
            "rarity": won.rarity,
            "emoji": won.emoji,
        },
        "obtained_at": obtained_at,
        "coins": new_coins,
    })


@route("GET", "/api/box")
def box(h: GachaHandler) -> None:
    with get_conn() as conn:
        user = h.require_user(conn)
        with conn.cursor() as cur:
            # 同じキャラを複数回引けるので、character_id ごとに集計する
            cur.execute(
                """
                SELECT c.id, c.name, c.rarity, c.emoji,
                       COUNT(*)         AS count,
                       MIN(uc.obtained_at) AS first_obtained_at,
                       MAX(uc.obtained_at) AS last_obtained_at
                  FROM user_characters uc
                  JOIN characters c ON c.id = uc.character_id
                 WHERE uc.user_id = %s
                 GROUP BY c.id
                 ORDER BY c.rarity DESC, c.id
                """,
                (user["id"],),
            )
            items = cur.fetchall()

            cur.execute(
                "SELECT COUNT(*) AS total_pulls FROM user_characters "
                "WHERE user_id = %s",
                (user["id"],),
            )
            total_pulls = cur.fetchone()["total_pulls"]

    h.send_json(200, {
        "user": user,
        "total_pulls": total_pulls,
        "items": items,
    })


# ---------------------------------------------------------------------------
# エントリポイント
# ---------------------------------------------------------------------------
def main() -> int:
    if not healthcheck():
        print("PostgreSQL に接続できません。`docker compose up -d` を先に。")
        return 1
    addr = ("0.0.0.0", APP_PORT)
    server = ThreadingHTTPServer(addr, GachaHandler)
    print(f"[gacha_gacha] listening on http://localhost:{APP_PORT}")
    print("  ルート一覧:")
    for (m, p) in sorted(ROUTES):
        print(f"    {m:5s} {p}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nbye")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
