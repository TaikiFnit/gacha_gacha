"""ch12 / step 4 — pickup_periods を考慮した抽選サーバ最小一式。

ゴール:
    Ch.5 で書いた fetch_pool() を「アクティブなピックアップ期間があれば、
    JSONB の倍率を掛ける」 仕様に差し替える。 抽選ロジック (重み付き乱択) 本体は
    一切変えない。

    POST /api/gacha/pull
        Body: {"gacha_id": int}
        → 200 {"character_id": int, "rarity": int}

実行:
    python exercises/ch12/step4_fetch_pool_lateral.py
    curl -X POST http://127.0.0.1:8001/api/gacha/pull \
         -H 'Authorization: Bearer 1' -H 'Content-Type: application/json' \
         -d '{"gacha_id": 1}'
"""
import json
import os
import random
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
    def __init__(self, status, message):
        super().__init__(message)
        self.status, self.message = status, message


def bad_request(m): return AppError(400, m)
def unauthorized(): return AppError(401, "認証が必要です")


ROUTES: dict = {}


def route(method, path):
    def deco(fn):
        ROUTES[(method, path)] = fn
        return fn
    return deco


def fetch_pool(conn, gacha_id):
    """期間限定 weight が乗った状態の (character_id, weight) 一覧を返す。"""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT gi.character_id,
                   c.rarity,
                   gi.weight * COALESCE(p.mult, 1) AS weight
              FROM gacha_items gi
              JOIN characters c ON c.id = gi.character_id
              LEFT JOIN LATERAL (
                    SELECT (pp.weights ->> gi.character_id::text)::numeric AS mult
                      FROM pickup_periods pp
                     WHERE pp.gacha_id = gi.gacha_id
                       AND NOW() <@ pp.period
                       AND pp.weights ? gi.character_id::text
                     LIMIT 1
                   ) p ON TRUE
             WHERE gi.gacha_id = %s
            """,
            (gacha_id,),
        )
        return cur.fetchall()


def weighted_choice(items):
    """Ch.5 と同じ重み付き乱択。 ロジックは変えない。"""
    total = sum(float(it["weight"]) for it in items)
    r = random.uniform(0, total)
    cum = 0.0
    for it in items:
        cum += float(it["weight"])
        if r <= cum:
            return it
    return items[-1]


@route("POST", "/api/gacha/pull")
def pull(h):
    body = h._read_json()
    gacha_id = body.get("gacha_id")
    if not isinstance(gacha_id, int):
        raise bad_request("gacha_id (int) が必要")

    with get_conn() as conn:
        h.require_user(conn)
        pool = fetch_pool(conn, gacha_id)
        if not pool:
            raise bad_request("そのガチャは存在しないか、 排出設定が空")
        chosen = weighted_choice(pool)
    h._json(200, {
        "character_id": chosen["character_id"],
        "rarity": chosen["rarity"],
    })


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

    def _read_json(self):
        n = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(n) if n else b""
        try:
            return json.loads(raw.decode("utf-8")) if raw else {}
        except json.JSONDecodeError as e:
            raise bad_request(f"invalid json: {e}")

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
