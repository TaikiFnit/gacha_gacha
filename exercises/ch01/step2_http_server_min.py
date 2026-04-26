"""ch01 / step 2 — http.server で最小の Hello サーバー。

ゴール:
    ヘッダのパースを毎回手書きしなくて済むよう、Python標準の
    http.server に乗り換える。BaseHTTPRequestHandler が do_GET を
    呼んでくれることを確認する。

実行:
    python exercises/ch01/step2_http_server_min.py
    curl -v http://127.0.0.1:8001/
    curl -v http://127.0.0.1:8001/anything

宿題:
    1. send_header("Content-Type", "...") の値を text/html に変えて、
       <h1>hello</h1> を返してみよう。ブラウザで開くと太字になる?
    2. self.send_response(200) を 418 に変えると、curl は何と表示する?
"""

from http.server import BaseHTTPRequestHandler, HTTPServer


class Hello(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        body = b"hello, http\n"
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    addr = ("127.0.0.1", 8001)
    print(f"listening on http://{addr[0]}:{addr[1]}")
    HTTPServer(addr, Hello).serve_forever()


if __name__ == "__main__":
    main()
