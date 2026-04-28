"""ch11 / step 5 — /api/me の先頭で collect() を自動的に呼ぶ最小サーバ。

ゴール:
    coins を読むエンドポイントは、 必ず最初に collect() を通す。
    ここでは /api/me だけ実装するが、 /api/box, /api/gacha/pull, /api/daily/claim
    にも同じパターンを適用するのが本物の運用。

    呼び忘れ防止のため、 ミドルウェア的に「認証直後に必ず呼ぶ」 ようにしている。

実行:
    python exercises/ch11/step5_endpoint_with_collect.py
    # 別ターミナル
    curl http://127.0.0.1:8001/api/me -H 'Authorization: Bearer 1'
    # 数十秒後にもう一度
    curl http://127.0.0.1:8001/api/me -H 'Authorization: Bearer 1'
    # → coins が経過秒数 × rate だけ増えているはず
"""
import json
import os
import traceback
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

import psycopg
from psycopg.rows import dict_row

DSN = os.environ.get(
    "DATABASE_URL",
    "host=127.0.0.1 port=5432 user=gacha password=gacha dbname=gacha",
)


def get_conn():
    return psycopg.connect(DSN, row_factory=dict_row)


class AppError(Exception):
    def __init__(self, status, message):
        super().__init__(message)
        self.status, self.message = status, message


def unauthorized(): return AppError(401, "認証が必要です")


ROUTES: dict = {}


def route(method, path):
    def deco(fn):
        ROUTES[(method, path)] = fn
        return fn
    return deco


def collect(conn, user_id: int) -> int:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT u.last_collected_at,
                   COALESCE(SUM(c.rarity), 0) AS rate
              FROM users u
              LEFT JOIN equipped_characters ec ON ec.user_id = u.id
              LEFT JOIN characters         c  ON c.id        = ec.character_id
             WHERE u.id = %s
             GROUP BY u.id
             FOR UPDATE OF u
            """,
            (user_id,),
        )
        row = cur.fetchone()
        if row is None:
            return 0
        elapsed = (datetime.now(timezone.utc) - row["last_collected_at"]).total_seconds()
        gained = int(elapsed * row["rate"])
        if gained > 0:
            cur.execute(
                "UPDATE users "
                "   SET coins = coins + %s, last_collected_at = NOW() "
                " WHERE id = %s",
                (gained, user_id),
            )
        return gained


@route("GET", "/api/me")
def me(h):
    with get_conn() as conn:
        user = h.require_user(conn)
        gained = collect(conn, user["id"])
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, name, coins, last_collected_at FROM users WHERE id = %s",
                (user["id"],),
            )
            me_row = cur.fetchone()
    h._json(200, {**me_row, "gained_just_now": gained})


class App(BaseHTTPRequestHandler):
    def do_GET(self):  self._dispatch("GET")    # noqa: N802
    def do_POST(self): self._dispatch("POST")   # noqa: N802

    def _dispatch(self, method):
        path = urlparse(self.path).path
        handler = ROUTES.get((method, path))
        if handler is None:
            return self._json(404, {"error": "Not Found", "path": path})
        try:
            handler(self)
        except AppError as e:
            self._json(e.status, {"error": e.message})
        except Exception as e:  # noqa: BLE001
            traceback.print_exc()
            self._json(500, {"error": "internal", "detail": str(e)})

    def require_user(self, conn):
        auth = self.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            raise unauthorized()
        try:
            uid = int(auth.split()[1])
        except (ValueError, IndexError):
            raise unauthorized()
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM users WHERE id = %s", (uid,))
            if cur.fetchone() is None:
                raise unauthorized()
        return {"id": uid}

    def _json(self, status, obj):
        body = json.dumps(obj, default=str, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        print(f"[{self.command}] {self.path}")


def main():
    addr = ("127.0.0.1", 8001)
    print(f"listening on http://{addr[0]}:{addr[1]}  (Ctrl+C で終了)")
    ThreadingHTTPServer(addr, App).serve_forever()


if __name__ == "__main__":
    main()
