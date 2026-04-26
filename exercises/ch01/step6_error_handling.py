"""ch01 / step 6 — 例外を「ステータス付きエラー」に変換する。

ゴール:
    ハンドラ側で `raise bad_request("...")` と書くと、自動的に
    400 + {"error": "..."} の JSON が返る形を作る。
    予期しないバグは 500 + traceback ログに流す。
    ここまでくると、サーバー本体 server/app.py の構造とほぼ同じになる。

実装する API:
    GET  /api/health
    POST /api/sum   { "a": <number>, "b": <number> }
        - a, b が無い -> 400
        - a, b が数値でない -> 400
        - 他は 200 で {"answer": a+b}

実行:
    python exercises/ch01/step6_error_handling.py
    curl -X POST http://127.0.0.1:8001/api/sum \\
         -H 'Content-Type: application/json' -d '{"a":1,"b":2}'
    curl -X POST http://127.0.0.1:8001/api/sum \\
         -H 'Content-Type: application/json' -d '{"a":"hi","b":2}'

宿題:
    1. unauthorized()  (= 401) ヘルパを作って、Cookie が無いときに投げてみよう
       (まだ cookie の値は使わなくて良い。ヘッダにそもそも Cookie が無いなら 401)
    2. server/app.py の AppError と _dispatch を比較してみよう。同じ作りになっているはず
"""

import json
import traceback
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Callable
from urllib.parse import urlparse


class AppError(Exception):
    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status, self.message = status, message


def bad_request(msg: str) -> AppError: return AppError(400, msg)
def not_found(msg: str = "Not Found") -> AppError: return AppError(404, msg)


ROUTES: dict[tuple[str, str], Callable[["App"], None]] = {}


def route(method: str, path: str):
    def deco(fn):
        ROUTES[(method.upper(), path)] = fn
        return fn
    return deco


@route("GET", "/api/health")
def health(h: "App") -> None:
    h._json(200, {"status": "ok"})


@route("POST", "/api/sum")
def add(h: "App") -> None:
    body = h._read_json()
    if "a" not in body or "b" not in body:
        raise bad_request("a と b が必要")
    a, b = body["a"], body["b"]
    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        raise bad_request("a と b は数値で")
    h._json(200, {"answer": a + b})


class App(BaseHTTPRequestHandler):
    def do_GET(self):    self._dispatch("GET")     # noqa: N802
    def do_POST(self):   self._dispatch("POST")    # noqa: N802

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
            self._json(500, {"error": "internal server error",
                             "detail": str(e)})

    def _read_json(self) -> dict:
        n = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(n) if n else b""
        try:
            return json.loads(raw.decode("utf-8")) if raw else {}
        except json.JSONDecodeError as e:
            raise bad_request(f"invalid json: {e}")

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
    HTTPServer(addr, App).serve_forever()


if __name__ == "__main__":
    main()
