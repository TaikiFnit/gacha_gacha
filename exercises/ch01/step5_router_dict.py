"""ch01 / step 5 — ルーター辞書でディスパッチをデータ駆動にする。

ゴール:
    do_GET 内の if/elif の山をやめて、(method, path) -> handler の
    辞書でディスパッチする方式に書き換える。
    ここで初めて「フレームワークっぽいもの」を手作りする感覚に到達する。

実装する API:
    GET  /api/health -> {"status": "ok"}
    POST /api/echo   -> {"received": ..., "size": ...}
    POST /api/sum    -> {"answer": a+b}

実行:
    python exercises/ch01/step5_router_dict.py
    curl http://127.0.0.1:8001/api/health
    curl -X POST http://127.0.0.1:8001/api/echo \\
         -H 'Content-Type: application/json' -d '{"x":1}'

宿題:
    1. @route("DELETE", "/api/echo") を増やして、204 No Content を返すハンドラを書こう
    2. ルートが見つからない場合の 404 を、「存在するルート一覧」を含む JSON に拡張しよう
"""

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Callable
from urllib.parse import urlparse


# (method, path) -> handler
ROUTES: dict[tuple[str, str], Callable[["App"], None]] = {}


def route(method: str, path: str):
    def deco(fn):
        ROUTES[(method.upper(), path)] = fn
        return fn
    return deco


@route("GET", "/api/health")
def health(h: "App") -> None:
    h._json(200, {"status": "ok"})


@route("POST", "/api/echo")
def echo(h: "App") -> None:
    body = h._read_json()
    h._json(200, {"received": body,
                  "size": len(json.dumps(body).encode())})


@route("POST", "/api/sum")
def add(h: "App") -> None:
    body = h._read_json()
    h._json(200, {"answer": body["a"] + body["b"]})


class App(BaseHTTPRequestHandler):
    def do_GET(self):    self._dispatch("GET")     # noqa: N802
    def do_POST(self):   self._dispatch("POST")    # noqa: N802

    def _dispatch(self, method: str) -> None:
        path = urlparse(self.path).path
        handler = ROUTES.get((method, path))
        if handler is None:
            return self._json(404, {"error": "Not Found",
                                    "available": [
                                        f"{m} {p}" for (m, p) in sorted(ROUTES)
                                    ]})
        handler(self)

    # ---- helpers --------------------------------------------------------
    def _read_json(self) -> dict:
        n = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(n) if n else b""
        return json.loads(raw.decode("utf-8")) if raw else {}

    def _json(self, status: int, obj: dict) -> None:
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    addr = ("127.0.0.1", 8001)
    print(f"listening on http://{addr[0]}:{addr[1]}")
    print("  routes:")
    for (m, p) in sorted(ROUTES):
        print(f"    {m} {p}")
    HTTPServer(addr, App).serve_forever()


if __name__ == "__main__":
    main()
