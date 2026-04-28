"""ch13 / step 5 — 認可チェック付きの GET /api/users/<id>/box 最小サーバ。

ゴール:
    「自分の Box は常に見える、 他人の Box は public_box=TRUE のときだけ見える」
    を 1 つのエンドポイントで実装する。 認可チェックは SQL ではなく、
    取得後の if 文で 1 行で書く方が読みやすい。

実行:
    python exercises/ch13/step5_view_box_with_authz.py
    curl http://127.0.0.1:8001/api/users/1/box -H 'Authorization: Bearer 1'   # 自分なので 200
    curl http://127.0.0.1:8001/api/users/2/box -H 'Authorization: Bearer 1'   # public_box 次第
"""
import json
import os
import re
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


def unauthorized(): return AppError(401, "認証が必要です")
def forbidden(m="権限がありません"): return AppError(403, m)
def not_found(m="Not Found"): return AppError(404, m)


PATH_RE = re.compile(r"^/api/users/(\d+)/box$")


def _view_box(h, target_id: int):
    with get_conn() as conn:
        viewer = h.require_user(conn)
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, name, public_box FROM users WHERE id = %s",
                (target_id,),
            )
            target = cur.fetchone()
            if target is None:
                raise not_found()
            if target["id"] != viewer["id"] and not target["public_box"]:
                raise forbidden("この Box は非公開です")
            cur.execute(
                "SELECT character_id, COUNT(*) AS n "
                "  FROM user_characters WHERE user_id = %s "
                " GROUP BY character_id ORDER BY character_id",
                (target_id,),
            )
            box = cur.fetchall()
    h._json(200, {"user_id": target["id"], "name": target["name"], "box": box})


class App(BaseHTTPRequestHandler):
    def do_GET(self):  self._dispatch("GET")    # noqa: N802
    def do_POST(self): self._dispatch("POST")   # noqa: N802

    def _dispatch(self, method):
        path = urlparse(self.path).path
        try:
            if method == "GET":
                m = PATH_RE.match(path)
                if m:
                    return _view_box(self, int(m.group(1)))
            self._json(404, {"error": "Not Found", "path": path})
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
