"""ch15 / step 4 — Prometheus 互換の /api/metrics を手書きで実装。

ゴール:
    リクエスト数 (counter) と累計レイテンシ (sum) を出すだけの最小実装。
    本番は prometheus_client パッケージに任せるのが楽。

実行:
    python exercises/ch15/step4_metrics_endpoint.py
    curl http://127.0.0.1:8001/api/metrics
"""
import json
import os
import sys
import time
import traceback
from collections import Counter
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from step1_json_logger import setup_logging   # noqa: E402

setup_logging()


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
def health(h): h._json(200, {"status": "ok"})


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
                traceback.print_exc()
                self._json(500, {"error": "internal"})
        finally:
            _record(method, path, status, time.perf_counter() - started)

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
