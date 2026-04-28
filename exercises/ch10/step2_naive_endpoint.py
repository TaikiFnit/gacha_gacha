"""ch10 / step 2 — 「SELECT してから INSERT」 の素朴版 (わざと壊す)。

ゴール:
    daily-claim を最も素直に書く。 1 リクエストずつ来る分には正しく動く。
    でも次の step4 で 2 本同時に投げると両方通ってしまうバグを抱えている。

実行:
    psql "$DATABASE_URL" -f exercises/ch10/step1_daily_bonuses_table.sql   # 先にテーブル作成
    python exercises/ch10/step2_naive_endpoint.py
    # 別ターミナル
    curl -X POST http://127.0.0.1:8001/api/daily/claim -H 'Authorization: Bearer 1'
    curl -X POST http://127.0.0.1:8001/api/daily/claim -H 'Authorization: Bearer 1'  # 400 になる

落とし穴:
    SELECT で「行が無い」 を確認した <em>瞬間</em> と INSERT する <em>瞬間</em> の間に、
    別トランザクションが INSERT してしまえる = TOCTTOU バグ。
    step3 で UNIQUE 制約に守らせて直す。
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


# ---------------- ルーティング + エラー ----------------
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


# ---------------- ハンドラ ----------------
@route("POST", "/api/daily/claim")
def claim_daily_naive(h: "App") -> None:
    AMOUNT = 200
    with get_conn() as conn:
        user = h.require_user(conn)
        with conn.cursor() as cur:
            # 1. 今日の行があるか確認
            cur.execute(
                "SELECT 1 FROM daily_bonuses "
                "WHERE user_id = %s "
                "  AND claimed_on = (CURRENT_DATE AT TIME ZONE 'Asia/Tokyo')::date",
                (user["id"],),
            )
            if cur.fetchone() is not None:
                raise bad_request("今日のボーナスはもう受け取り済みです")
            # 2. 無ければ INSERT (← この間に他のリクエストが入ると壊れる)
            cur.execute(
                "INSERT INTO daily_bonuses (user_id, amount) VALUES (%s, %s)",
                (user["id"], AMOUNT),
            )
    h._json(200, {"amount": AMOUNT, "warning": "naive 実装。 step4 で壊れます"})


# ---------------- HTTP サーバ本体 ----------------
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
        # 学習用: Authorization: Bearer <user_id> をそのまま user_id として扱う
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
        print(f"[{self.command}] {self.path} -> ?")


def main():
    addr = ("127.0.0.1", 8001)
    print(f"listening on http://{addr[0]}:{addr[1]}  (Ctrl+C で終了)")
    ThreadingHTTPServer(addr, App).serve_forever()


if __name__ == "__main__":
    main()
