"""ch10 / step 3 — UNIQUE 制約で物理的に二重を弾く版。

ゴール:
    step2 の TOCTTOU バグを直す。 「SELECT で確認」 を捨て、 INSERT 一発を
    UNIQUE 制約に守ってもらう。 二重なら DB が UniqueViolation を投げてくれるので、
    アプリ側はそれを 400 に翻訳するだけ。

実行:
    python exercises/ch10/step3_unique_safe_endpoint.py
    curl -X POST http://127.0.0.1:8001/api/daily/claim -H 'Authorization: Bearer 1'
    curl -X POST http://127.0.0.1:8001/api/daily/claim -H 'Authorization: Bearer 1'  # 400
"""
import json
import os
import traceback
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
    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status, self.message = status, message


def bad_request(m: str) -> AppError: return AppError(400, m)
def unauthorized() -> AppError: return AppError(401, "認証が必要です")


ROUTES: dict = {}


def route(method: str, path: str):
    def deco(fn):
        ROUTES[(method, path)] = fn
        return fn
    return deco


@route("POST", "/api/daily/claim")
def claim_daily(h: "App") -> None:
    AMOUNT = 200
    with get_conn() as conn:
        user = h.require_user(conn)
        with conn.cursor() as cur:
            try:
                cur.execute(
                    """
                    INSERT INTO daily_bonuses (user_id, amount) VALUES (%s, %s)
                    RETURNING claimed_on
                    """,
                    (user["id"], AMOUNT),
                )
                claimed_on = cur.fetchone()["claimed_on"]
            except psycopg.errors.UniqueViolation:
                raise bad_request("今日のボーナスはもう受け取り済みです")
    h._json(200, {"amount": AMOUNT, "claimed_on": claimed_on})


class App(BaseHTTPRequestHandler):
    def do_GET(self):  self._dispatch("GET")    # noqa: N802
    def do_POST(self): self._dispatch("POST")   # noqa: N802

    def _dispatch(self, method: str) -> None:
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
            cur.execute("SELECT id, name, coins FROM users WHERE id = %s", (uid,))
            user = cur.fetchone()
            if user is None:
                raise unauthorized()
            return user

    def _json(self, status: int, obj: dict) -> None:
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
