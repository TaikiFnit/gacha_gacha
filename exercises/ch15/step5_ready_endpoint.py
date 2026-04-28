"""ch15 / step 5 — readiness probe (DB 接続まで含めた健康チェック)。

ゴール:
    /api/health : プロセスが生きていれば 200
    /api/ready  : DB に SELECT 1 が通れば 200、 失敗なら 503

    Kubernetes の readiness probe を /api/ready に紐付けると、
    DB 起動待ちの間に LB からトラフィックを流さない、 が実現できる。

実行:
    python exercises/ch15/step5_ready_endpoint.py
    curl http://127.0.0.1:8001/api/health
    curl http://127.0.0.1:8001/api/ready
    # docker compose stop db のあと curl /api/ready が 503 を返すのを確認
"""
import json
import os
import sys
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

import psycopg

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from step1_json_logger import setup_logging   # noqa: E402

setup_logging()

DSN = os.environ.get(
    "DATABASE_URL",
    "host=127.0.0.1 port=5432 user=gacha password=gacha dbname=gacha",
)


ROUTES: dict = {}


def route(method, path):
    def deco(fn):
        ROUTES[(method, path)] = fn
        return fn
    return deco


@route("GET", "/api/health")
def health(h): h._json(200, {"status": "ok"})


@route("GET", "/api/ready")
def ready(h):
    try:
        with psycopg.connect(DSN, connect_timeout=2) as conn, conn.cursor() as cur:
            cur.execute("SELECT 1")
        h._json(200, {"status": "ready"})
    except Exception as e:  # noqa: BLE001
        h._json(503, {"status": "not ready", "detail": str(e)})


class App(BaseHTTPRequestHandler):
    def do_GET(self):  self._dispatch("GET")    # noqa: N802

    def _dispatch(self, method):
        path = urlparse(self.path).path
        handler = ROUTES.get((method, path))
        try:
            if handler is None:
                return self._json(404, {"error": "Not Found"})
            handler(self)
        except Exception:  # noqa: BLE001
            traceback.print_exc()
            self._json(500, {"error": "internal"})

    def _json(self, status, obj):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        pass


def main():
    addr = ("127.0.0.1", 8001)
    print(f"listening on http://{addr[0]}:{addr[1]}")
    ThreadingHTTPServer(addr, App).serve_forever()


if __name__ == "__main__":
    main()
