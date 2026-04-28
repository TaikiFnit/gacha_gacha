"""ch16 / step 6 — フロント刷新時の API 互換性 smoke テスト。

ゴール:
    フロントを React / Vue / Svelte に書き換えても、 サーバ側の API が
    壊れていないことを確認するための独立テスト。 「API は契約」 という章の
    主張をコードで担保する。

実行 (本物のサーバ起動中に):
    python -m server.app  # 別ターミナルで
    python exercises/ch16/step6_api_smoke.py
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request

URL = os.environ.get("BASE_URL", "http://127.0.0.1:8000")


def _req(method: str, path: str, body=None, token: str | None = None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(
        URL + path, data=data, headers=headers, method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status, json.loads(r.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8") or "{}")


def expect(name: str, ok: bool, detail=None):
    if ok:
        print(f"  PASS  {name}")
    else:
        print(f"  FAIL  {name}  {detail!r}")
        sys.exit(1)


def main():
    print(f"smoke against {URL}")
    suffix = str(int(time.time()))   # 毎回ユニークな名前
    name = f"smoke_{suffix}"
    pw = "p"

    s, b = _req("POST", "/api/register", {"name": name, "password": pw})
    expect("register 200", s == 200, b)

    s, b = _req("POST", "/api/login", {"name": name, "password": pw})
    expect("login 200 with token", s == 200 and "token" in b, b)
    token = b["token"]

    s, b = _req("GET", "/api/me", token=token)
    expect("me 200 with coins", s == 200 and "coins" in b, b)

    s, b = _req("GET", "/api/gacha/list")
    expect("gacha list 200", s == 200, b)

    if isinstance(b, list) and b:
        gacha_id = b[0]["id"]
        s, b = _req("POST", "/api/gacha/pull", {"gacha_id": gacha_id}, token=token)
        expect("pull 200", s == 200 and "character" in b, b)

    s, b = _req("GET", "/api/box", token=token)
    expect("box 200", s == 200, b)

    s, b = _req("POST", "/api/logout", token=token)
    expect("logout 200", s == 200, b)

    print("\nALL PASS")


if __name__ == "__main__":
    main()
