"""ch15 / step 6 — 構造化ログ + アクセスログ + metrics + ready の最小サーバ。

ゴール:
    step1〜5 の要素を 1 ファイルに統合した「観測しやすい」 サーバ。
    Ch.15 の最終形。

実行:
    python exercises/ch15/step6_full_observable_server.py
    curl http://127.0.0.1:8001/api/health
    curl http://127.0.0.1:8001/api/ready
    curl http://127.0.0.1:8001/api/metrics
"""
import json
import logging
import os
import sys
import time
import traceback
from collections import Counter
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

import psycopg

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from step1_json_logger import setup_logging   # noqa: E402

setup_logging()
log = logging.getLogger("gacha")

DSN = os.environ.get(
    "DATABASE_URL",
    "host=127.0.0.1 port=5432 user=gacha password=gacha dbname=gacha",
)


_METRICS = {
    "requests_total":   Counter(),
    "request_seconds":  [],
}


def _record(method, path, status, sec):
    _METRICS["requests_total"][(method, path, status)] += 1
    _METRICS["request_seconds"].append(sec)


ROUTES: dict = {}


def route(method, path):
    def deco(fn):
        ROUTES[(method, path)] = fn
        return fn
    return deco


@route("GET", "/api/health")
def health(h):
    h._json(200, {"status": "ok"})


@route("GET", "/api/ready")
def ready(h):
    try:
        with psycopg.connect(DSN, connect_timeout=2) as conn, conn.cursor() as cur:
            cur.execute("SELECT 1")
        h._json(200, {"status": "ready"})
    except Exception as e:  # noqa: BLE001
        log.warning("not ready", extra={"ctx_err": str(e)})
        h._json(503, {"status": "not ready", "detail": str(e)})


@route("GET", "/api/metrics")
def metrics(h):
    lines = ["# TYPE gacha_requests_total counter"]
    for (m, p, s), n in _METRICS["requests_total"].items():
        lines.append(
            f'gacha_requests_total{{method="{m}",path="{p}",status="{s}"}} {n}'
        )
    lines.append("# TYPE gacha_request_seconds_sum gauge")
    lines.append(f'gacha_request_seconds_sum {sum(_METRICS["request_seconds"]):.6f}')
    body = ("\n".join(lines) + "\n").encode("utf-8")
    h.send_response(200)
    h.send_header("Content-Type", "text/plain; version=0.0.4")
    h.send_header("Content-Length", str(len(body)))
    h.end_headers()
    h.wfile.write(body)


class App(BaseHTTPRequestHandler):
    def do_GET(self):  self._dispatch("GET")    # noqa: N802

    def _dispatch(self, method):
        started = time.perf_counter()
        path = urlparse(self.path).path
        handler = ROUTES.get((method, path))
        status = 200
        try:
            if handler is None:
                status = 404
                return self._json(404, {"error": "Not Found"})
            try:
                handler(self)
            except Exception:  # noqa: BLE001
                status = 500
                log.exception("unhandled", extra={"ctx_path": path})
                self._json(500, {"error": "internal"})
        finally:
            sec = time.perf_counter() - started
            _record(method, path, status, sec)
            log.info("access", extra={
                "ctx_method": method,
                "ctx_path":   path,
                "ctx_status": status,
                "ctx_ms":     round(sec * 1000, 2),
            })

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
    log.info("listen", extra={"ctx_url": f"http://{addr[0]}:{addr[1]}"})
    ThreadingHTTPServer(addr, App).serve_forever()


if __name__ == "__main__":
    main()
