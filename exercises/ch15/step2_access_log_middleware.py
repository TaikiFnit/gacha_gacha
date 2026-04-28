"""ch15 / step 2 — アクセスログをミドルウェア的に全 API へ自動付与。

ゴール:
    method, path, status, ms を 1 行 JSON で必ず出す。 try/finally で
    成功でも失敗でも 1 行残す。

実行:
    python exercises/ch15/step2_access_log_middleware.py
    curl http://127.0.0.1:8001/api/health
    curl http://127.0.0.1:8001/api/whoami
    # ↑ サーバ側に { "method": "GET", "path": "...", "status": ..., "ms": ... } が出る
"""
import json
import logging
import os
import sys
import time
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from step1_json_logger import setup_logging   # noqa: E402

setup_logging()
log = logging.getLogger("gacha")


ROUTES: dict = {}


def route(method, path):
    def deco(fn):
        ROUTES[(method, path)] = fn
        return fn
    return deco


class AppError(Exception):
    def __init__(self, status, message):
        super().__init__(message)
        self.status, self.message = status, message


@route("GET", "/api/health")
def health(h): h._json(200, {"status": "ok"})


@route("GET", "/api/boom")
def boom(h): raise RuntimeError("intentional crash for log demo")


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
                return self._json(404, {"error": "Not Found", "path": path})
            try:
                handler(self)
            except AppError as e:
                status = e.status
                self._json(e.status, {"error": e.message})
            except Exception as e:  # noqa: BLE001
                status = 500
                log.exception("unhandled", extra={"ctx_path": path})
                self._json(500, {"error": "internal"})
        finally:
            log.info("access", extra={
                "ctx_method": method,
                "ctx_path":   path,
                "ctx_status": status,
                "ctx_ms":     round((time.perf_counter() - started) * 1000, 2),
            })

    def _json(self, status, obj):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        pass   # 標準のアクセスログを止めて、 JSON 側に一本化


def main():
    addr = ("127.0.0.1", 8001)
    log.info("listen", extra={"ctx_url": f"http://{addr[0]}:{addr[1]}"})
    ThreadingHTTPServer(addr, App).serve_forever()


if __name__ == "__main__":
    main()
