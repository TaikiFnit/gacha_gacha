"""Build gacha_gacha.ipynb from the existing source files in the repo.

Run:
    python tools/build_notebook.py

The notebook is generated from this script + the actual files in
db/, server/, web/, exercises/. When you change those files, just
re-run this builder to regenerate the notebook.

The notebook is designed to:
  - Run end-to-end on Colab (or locally) without prior setup
  - Use SQLite by default (zero install)
  - Build up the production file tree via %%writefile cells
  - Eventually start the real server/app.py in a thread and let
    the learner play the gacha frontend inside the notebook
"""

from __future__ import annotations

import json
import pathlib
import textwrap

ROOT = pathlib.Path(__file__).resolve().parent.parent
NB_PATH = ROOT / "gacha_gacha.ipynb"


# ---------------------------------------------------------------------------
# cell builders
# ---------------------------------------------------------------------------
def md(text: str) -> dict:
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": text.rstrip() + "\n",
    }


def code(src: str) -> dict:
    return {
        "cell_type": "code",
        "metadata": {},
        "execution_count": None,
        "outputs": [],
        "source": src.rstrip() + "\n",
    }


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8").rstrip() + "\n"


def writefile(path: str, body: str) -> dict:
    """A %%writefile cell that materialises a file with the given body."""
    return code(f"%%writefile {path}\n" + body)


# ---------------------------------------------------------------------------
# notebook cells
# ---------------------------------------------------------------------------
cells: list[dict] = []


# ============================================================================
# 0. はじめに
# ============================================================================
cells += [
    md("""# gacha_gacha — ガチャシステムでデータベースとバックエンドを動かしながら学ぶ

本 Notebook は **Colab で上から順に実行する** だけで、ガチャゲームのバックエンド一式が
組み上がり、ノートブックの中で実際にガチャを回せるようになる学習教材です。

## ねらい

- HTTP サーバー / SQL / Python ガチャ抽選 を、フレームワークの魔法に頼らず
  「自分で書く感覚」 で身につける
- AI に書かせて読むだけだと身につかない → **コピペでも手書きでも、実際にコードが動く** 状態を経験する
- 章を進めるごとに、最終的なフルセット (`server/app.py` + `db/schema.sql` + `web/index.html`)
  が、目の前で 1 ファイルずつ仕上がっていく

## 対象

- プログラミング経験 1〜2 年 (Java / Kotlin など)
- Python は構文が読める程度で OK
- データベースは PK/FK を聞いた程度の前提

## 進め方

1. **上から順に実行** (Shift+Enter)。 各セルの出力を見ながら進む
2. 気が向いたらセルを書き換えて壊してみる。動かなくなったら戻して再実行
3. 最終セクションでガチャ画面が Notebook 内に現れたら完走

## DB について

この Notebook は 学習を最短で始めるため **SQLite** を使います (Python 標準ライブラリ、追加インストール不要)。
本格的な PostgreSQL 環境はリポジトリ直下の `docker-compose.yml` に用意してあり、
コードを変えずに切り替え可能です (最終章で説明)。
"""),
]


# ============================================================================
# 1. 環境セットアップ
# ============================================================================
cells += [
    md("""---
## 第 0 章 — 環境セットアップ

このセクションを実行すると、Notebook が動いている場所の下に
`gacha_gacha/` という作業フォルダができ、そこに章ごとのファイルを書き込んでいきます。

> Colab なら `/content/gacha_gacha` に作られます。ローカルで実行している場合は
> 現在のディレクトリ直下に作られます。
"""),
    code("""import os, pathlib, sys

# Colab かどうかで作業ディレクトリを変える
if pathlib.Path("/content").exists():
    ROOT = pathlib.Path("/content/gacha_gacha")
else:
    ROOT = pathlib.Path.cwd() / "gacha_gacha_workspace"
ROOT.mkdir(exist_ok=True, parents=True)

# 必要なサブディレクトリを作る
for sub in ["db", "server", "web", "exercises/ch01", "exercises/ch02"]:
    (ROOT / sub).mkdir(exist_ok=True, parents=True)

# 以降のセルから相対パスで使えるように移動
os.chdir(ROOT)
print("作業ディレクトリ:", ROOT)
print("中身:", sorted(p.name for p in ROOT.iterdir()))

# server/ をモジュールとして import できるようにパスを通す
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
"""),
]


# ============================================================================
# 2. 第1章 HTTPサーバー
# ============================================================================
cells += [
    md("""---
# 第 1 章 — HTTPサーバーを建ててみよう

最終的にはガチャの API になりますが、いきなり API は建てません。
**1 番下の TCP ソケットから始めて、6 ステップで API の足場を組みます**。

最後 (Step 6) のコードは、本物の `server/app.py` の骨格とほぼ同じになります。

## HTTP は「一往復のテキスト」

クライアントが手紙を 1 通送り、サーバーが返事を 1 通返す。
手紙の中身はただのテキスト。実物はこんな形:

```
POST /api/login HTTP/1.1
Host: localhost:8000
Content-Type: application/json
Content-Length: 39

{"name":"alice","password":"secret"}
```

```
HTTP/1.1 200 OK
Content-Type: application/json; charset=utf-8
Content-Length: 24

{"user":{"id":1,"name":"alice"}}
```

これだけです。ヘッダ + 空行 + 本文。Web の上で動いているもの全て、この往復の上に積み上がっています。
"""),
]

# --- Step 1 -----------------------------------------------------------------
cells += [
    md("""## Step 1 — TCP ソケットだけで HTTP風のテキストを返す

HTTP の前提として、TCP ソケットがバイト列を運んでいます。
Python の `socket` モジュールを使うと、その層から書けます。

下のセルを実行すると、ファイル `exercises/ch01/step1_socket.py` ができます。
そのあと、もう 1 つ下のセルでバックグラウンド起動 → curl 相当の確認まで自動で行います。
"""),
    writefile("exercises/ch01/step1_socket.py", read("exercises/ch01/step1_socket.py")),
    code("""# Step 1 を別スレッドで起動して、内部から確認する
import socket, threading, urllib.request, time

def step1_serve_once():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("127.0.0.1", 9000))
    s.listen()
    conn, _ = s.accept()
    raw = conn.recv(4096)
    print("---- received ----")
    print(raw.decode(errors="replace"))
    print("---- end ----")
    body = b"hello, raw tcp\\n"
    conn.sendall(b"HTTP/1.1 200 OK\\r\\n"
                 b"Content-Type: text/plain; charset=utf-8\\r\\n"
                 b"Content-Length: " + str(len(body)).encode() + b"\\r\\n"
                 b"\\r\\n" + body)
    conn.close()
    s.close()

t = threading.Thread(target=step1_serve_once, daemon=True)
t.start()
time.sleep(0.1)
resp = urllib.request.urlopen("http://127.0.0.1:9000/")
print("status:", resp.status)
print("body  :", resp.read().decode())
t.join(timeout=1)
"""),
    md("""**期待される出力 (抜粋):**
```
---- received ----
GET / HTTP/1.1
Accept-Encoding: identity
Host: 127.0.0.1:9000
...
---- end ----
status: 200
body  : hello, raw tcp
```

### 観察ポイント
- HTTP は「テキスト」であること (リクエストの中身が普通の英語+改行)
- `Content-Length` は応答ボディの**バイト数**。これが嘘だとクライアントが固まる
- ヘッダの後ろに**空行 (\\r\\n\\r\\n)** が必ず必要

### 宿題 (やってみよう)
1. `Content-Type` を `text/html` に変えて `<h1>hello</h1>` を返してみる
2. ステータスコードを `418` (I'm a teapot) にしてみる
"""),
]

# --- Step 2 -----------------------------------------------------------------
cells += [
    md("""## Step 2 — `http.server` で最小の Hello GET

Step 1 のように毎回ヘッダを手で書くのは辛い。
Python 標準の `http.server.BaseHTTPRequestHandler` に乗り換えます。
`do_GET` をオーバーライドすると GET 全般が捕まえられます。
"""),
    writefile("exercises/ch01/step2_http_server_min.py",
              read("exercises/ch01/step2_http_server_min.py")),
    code("""# Step 2 を別スレッドで起動 → 内部から GET して確認
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading, urllib.request, time

class Hello(BaseHTTPRequestHandler):
    def do_GET(self):
        body = b"hello, http\\n"
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
    def log_message(self, fmt, *args): pass  # quiet

server = HTTPServer(("127.0.0.1", 8001), Hello)
threading.Thread(target=server.serve_forever, daemon=True).start()
time.sleep(0.1)
for path in ["/", "/anything", "/api/foo"]:
    r = urllib.request.urlopen("http://127.0.0.1:8001" + path)
    print(path, "->", r.status, r.read())
server.shutdown()
"""),
    md("""**期待される出力:**
```
/ -> 200 b'hello, http\\n'
/anything -> 200 b'hello, http\\n'
/api/foo -> 200 b'hello, http\\n'
```

どのパスでも同じ応答が返るのに気付きましたか?
パスごとに分けるのが Step 3 です。
"""),
]

# --- Step 3 -----------------------------------------------------------------
cells += [
    md("""## Step 3 — パスで分岐 + クエリ文字列を受け取る

`self.path` は `"/api/echo?msg=hi"` のような形で来るので、
`urllib.parse.urlparse` でパスとクエリに分けます。
"""),
    writefile("exercises/ch01/step3_routing.py", read("exercises/ch01/step3_routing.py")),
    code("""# Step 3 を起動して 4 通りのパスを叩く
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import json, threading, urllib.request, time

class App(BaseHTTPRequestHandler):
    def do_GET(self):
        url = urlparse(self.path); path = url.path; q = parse_qs(url.query)
        if path == "/":              return self._text(200, "hello, http\\n")
        if path == "/api/health":    return self._json(200, {"status": "ok"})
        if path == "/api/echo":      return self._json(200, {"you_said": q.get("msg", [""])[0]})
        return self._json(404, {"error": "Not Found", "path": path})
    def _text(self, s, body):
        b = body.encode(); self.send_response(s)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
    def _json(self, s, obj):
        b = json.dumps(obj, ensure_ascii=False).encode(); self.send_response(s)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
    def log_message(self, fmt, *args): pass

server = HTTPServer(("127.0.0.1", 8002), App)
threading.Thread(target=server.serve_forever, daemon=True).start()
time.sleep(0.1)
for path in ["/", "/api/health", "/api/echo?msg=hello%20world", "/missing"]:
    try:
        r = urllib.request.urlopen("http://127.0.0.1:8002" + path)
        print(f"{path:35s} -> {r.status} {r.read().decode()[:60]}")
    except urllib.error.HTTPError as e:
        print(f"{path:35s} -> {e.code} {e.read().decode()[:60]}")
server.shutdown()
"""),
    md("""**期待される出力:**
```
/                                   -> 200 hello, http
/api/health                         -> 200 {"status": "ok"}
/api/echo?msg=hello%20world         -> 200 {"you_said": "hello world"}
/missing                            -> 404 {"error": "Not Found", "path": "/missing"}
```
"""),
]

# --- Step 4 -----------------------------------------------------------------
cells += [
    md("""## Step 4 — POST で JSON を受け取る

ガチャを引く API は POST します。
本文の長さは `Content-Length` ヘッダから読み取り、`self.rfile.read(n)` でバイト列を取得して JSON にデコードします。
"""),
    writefile("exercises/ch01/step4_post_json.py", read("exercises/ch01/step4_post_json.py")),
    code("""# Step 4 を起動して /api/sum に POST してみる
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse
import json, threading, urllib.request, time

class App(BaseHTTPRequestHandler):
    def do_POST(self):
        path = urlparse(self.path).path
        n = int(self.headers.get("Content-Length", "0"))
        try:
            body = json.loads(self.rfile.read(n).decode("utf-8")) if n else {}
        except json.JSONDecodeError as e:
            return self._json(400, {"error": f"invalid json: {e}"})
        if path == "/api/echo":
            return self._json(200, {"received": body, "size": n})
        if path == "/api/sum":
            try: a, b = body["a"], body["b"]
            except KeyError: return self._json(400, {"error": "a と b が必要"})
            return self._json(200, {"answer": a + b})
        return self._json(404, {"error": "Not Found"})
    def _json(self, s, obj):
        b = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(s)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
    def log_message(self, fmt, *args): pass

server = HTTPServer(("127.0.0.1", 8003), App)
threading.Thread(target=server.serve_forever, daemon=True).start()
time.sleep(0.1)

def post(path, payload):
    req = urllib.request.Request(
        "http://127.0.0.1:8003" + path,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST")
    try:
        return urllib.request.urlopen(req).read().decode()
    except urllib.error.HTTPError as e:
        return f"[{e.code}] " + e.read().decode()

print("echo:", post("/api/echo", {"name": "alice", "age": 7}))
print("sum :", post("/api/sum", {"a": 1, "b": 2}))
print("bad :", post("/api/sum", {"a": 1}))   # b 欠落で 400
server.shutdown()
"""),
    md("""**期待される出力:**
```
echo: {"received": {"name": "alice", "age": 7}, "size": 24}
sum : {"answer": 3}
bad : [400] {"error": "a と b が必要"}
```
"""),
]

# --- Step 5 -----------------------------------------------------------------
cells += [
    md("""## Step 5 — ルーター辞書でデータ駆動に

`do_GET` 内で if/elif の山を書くのは、ハンドラが増えると破綻します。
**`(method, path) → handler`** という辞書でディスパッチする形に書き換えます。
ここで初めて「フレームワークっぽいもの」を手作りした感覚になります。
"""),
    writefile("exercises/ch01/step5_router_dict.py", read("exercises/ch01/step5_router_dict.py")),
    md("""ポイント:
- `@route("GET", "/api/health")` というデコレータが `ROUTES` 辞書に登録する
- `do_GET` / `do_POST` は単に `_dispatch(method)` を呼ぶだけ
- `_dispatch` は `ROUTES.get((method, path))` でハンドラを取り出して呼ぶ
- このパターンは Flask, FastAPI, Express など、ありとあらゆる Web フレームワークの中身です
"""),
]

# --- Step 6 -----------------------------------------------------------------
cells += [
    md("""## Step 6 — 例外を JSON エラーに変換する

ハンドラ内で `raise bad_request("a と b は数値で")` と書くと、
**自動的に** 400 + `{"error": "..."}` が返る形を作ります。

予期せぬ例外は traceback を stderr に出して 500 を返す。
ここまで仕上がると、本物の `server/app.py` とほぼ同じ骨格になります。
"""),
    writefile("exercises/ch01/step6_error_handling.py", read("exercises/ch01/step6_error_handling.py")),
    code("""# Step 6 を起動して、正常系と異常系を両方確認
from exercises.ch01.step6_error_handling import App
from http.server import HTTPServer
import threading, urllib.request, urllib.error, json, time

server = HTTPServer(("127.0.0.1", 8006), App)
threading.Thread(target=server.serve_forever, daemon=True).start()
time.sleep(0.2)

def hit(method, path, body=None):
    req = urllib.request.Request(
        "http://127.0.0.1:8006" + path,
        data=json.dumps(body).encode() if body else None,
        headers={"Content-Type": "application/json"} if body else {},
        method=method)
    try:
        r = urllib.request.urlopen(req)
        return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()

print("健康 :", hit("GET", "/api/health"))
print("足し算:", hit("POST", "/api/sum", {"a": 1, "b": 2}))
print("型違反:", hit("POST", "/api/sum", {"a": "x", "b": 2}))
print("欠損 :", hit("POST", "/api/sum", {"a": 1}))
print("壊れ :", ("--", "(invalid json で 400 が返る:)"))
import urllib.request as ur
req = ur.Request("http://127.0.0.1:8006/api/sum",
                 data=b"not json", headers={"Content-Type": "application/json"},
                 method="POST")
try: ur.urlopen(req)
except urllib.error.HTTPError as e: print("        ", e.code, e.read().decode())

server.shutdown()
"""),
    md("""**期待される出力:**
```
健康 : (200, '{"status": "ok"}')
足し算: (200, '{"answer": 3}')
型違反: (400, '{"error": "a と b は数値で"}')
欠損 : (400, '{"error": "a と b が必要"}')
壊れ : (--, '(invalid json で 400 が返る:)')
         400 {"error": "invalid json: Expecting value: line 1 column 1 (char 0)"}
```

🎉 これで HTTP サーバーの足場が完成。
**`exercises/ch01/step6_error_handling.py` と `server/app.py` を見比べて**、
ほぼ同じ骨格になっていることを確認してから次へ。
"""),
]


# ============================================================================
# 3. 第2章 DB設計
# ============================================================================
cells += [
    md("""---
# 第 2 章 — データベース設計

ここからは SQL を打ちます。 Notebook 上で `sqlite3` モジュールを直接使い、
インメモリのデータベースに対して `CREATE TABLE` → `INSERT` → `SELECT` を順番に動かします。

> SQLite と PostgreSQL では一部記法が違いますが、本章で扱う範囲はほぼ同じです。
> `BIGSERIAL` (PG) ↔ `INTEGER PRIMARY KEY AUTOINCREMENT` (SQLite) のような違いだけ後で吸収します。
"""),
    code("""import sqlite3

# 1 つの接続を Notebook 全体で使い回す (= ステップが積み上がる)
conn = sqlite3.connect(":memory:")
conn.execute("PRAGMA foreign_keys = ON")  # SQLiteはデフォOFF。FKを効かせるため必須

def run(sql, params=()):
    \"\"\"SQL を実行して結果があれば表として表示するヘルパ。\"\"\"
    cur = conn.execute(sql, params)
    if cur.description:
        cols = [d[0] for d in cur.description]
        rows = cur.fetchall()
        print(" | ".join(cols))
        print("-+-".join("-" * len(c) for c in cols))
        for row in rows: print(" | ".join(str(v) for v in row))
        print(f"({len(rows)} rows)")
    else:
        print(f"OK ({cur.rowcount} rows affected)")

print("DB connected.")
"""),
]

# step1
cells += [
    md("""## Step 1 — `users` テーブルを作って遊ぶ

主キー、UNIQUE、CHECK、DEFAULT、NOT NULL — 制約のオンパレード。
"""),
    code("""run('''
CREATE TABLE users (
    id          INTEGER  PRIMARY KEY AUTOINCREMENT,
    name        TEXT     NOT NULL UNIQUE,
    pass_hash   TEXT     NOT NULL,
    coins       INTEGER  NOT NULL DEFAULT 1000 CHECK (coins >= 0),
    created_at  TEXT     NOT NULL DEFAULT (datetime('now'))
)
''')
"""),
    code("""run("INSERT INTO users (name, pass_hash) VALUES ('alice', 'fakehash1')")
run("INSERT INTO users (name, pass_hash) VALUES ('bob',   'fakehash2')")
run("INSERT INTO users (name, pass_hash) VALUES ('carol', 'fakehash3')")
run("SELECT id, name, coins, created_at FROM users ORDER BY id")
"""),
    code("""# 制約に殴られる体験
try:
    run("INSERT INTO users (name, pass_hash) VALUES ('alice', 'dup')")  # UNIQUE 違反
except Exception as e:
    print("UNIQUE 違反:", e)

try:
    run("UPDATE users SET coins = -1 WHERE name = 'alice'")  # CHECK 違反
except Exception as e:
    print("CHECK 違反:", e)
"""),
    md("""DB が「自分から間違いを教えてくれる」のが分かったでしょうか。
これがアプリ層に同じバリデーションを書かなくて済む理由です。
"""),
]

# step2
cells += [
    md("""## Step 2 — `characters` マスタを足す
"""),
    code("""run('''
CREATE TABLE characters (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    name    TEXT    NOT NULL UNIQUE,
    rarity  INTEGER NOT NULL CHECK (rarity BETWEEN 1 AND 5),
    emoji   TEXT    NOT NULL DEFAULT '❓'
)
''')

# データ投入
chars = [
    ('スライム', 1, '🟢'),
    ('ウルフ',   2, '🐺'),
    ('ナイト',   3, '🛡️'),
    ('ペガサス', 4, '🦄'),
    ('ドラゴン', 5, '🐉'),
]
conn.executemany("INSERT INTO characters (name, rarity, emoji) VALUES (?, ?, ?)", chars)

run("SELECT id, name, rarity, emoji FROM characters ORDER BY rarity DESC")
"""),
]

# step3
cells += [
    md("""## Step 3 — ガチャ筐体 + 排出設定 (多対多 + 重み)

「複数のガチャに、複数のキャラが、それぞれ違う重みで登場する」を
RDB で表現する常套手段が **中間テーブル**。さらに今回はそこに `weight` (重み) も持たせます。
"""),
    code("""run('''
CREATE TABLE gachas (
    id    INTEGER PRIMARY KEY AUTOINCREMENT,
    name  TEXT    NOT NULL UNIQUE,
    price INTEGER NOT NULL CHECK (price > 0)
)
''')

run('''
CREATE TABLE gacha_items (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    gacha_id     INTEGER NOT NULL REFERENCES gachas(id)     ON DELETE CASCADE,
    character_id INTEGER NOT NULL REFERENCES characters(id) ON DELETE RESTRICT,
    weight       INTEGER NOT NULL CHECK (weight > 0),
    UNIQUE (gacha_id, character_id)
)
''')

conn.executemany("INSERT INTO gachas (name, price) VALUES (?, ?)",
                 [('通常ガチャ', 100), ('プレミアムガチャ', 300)])

# 通常ガチャは全レア度をバランス良く
conn.execute('''
INSERT INTO gacha_items (gacha_id, character_id, weight)
SELECT g.id, c.id,
       CASE c.rarity WHEN 1 THEN 60 WHEN 2 THEN 30
                     WHEN 3 THEN 20 WHEN 4 THEN 8 WHEN 5 THEN 2 END
  FROM gachas g, characters c
 WHERE g.name = '通常ガチャ'
''')

# プレミアムは レア度3以上のみ
conn.execute('''
INSERT INTO gacha_items (gacha_id, character_id, weight)
SELECT g.id, c.id,
       CASE c.rarity WHEN 3 THEN 50 WHEN 4 THEN 20 WHEN 5 THEN 10 END
  FROM gachas g, characters c
 WHERE g.name = 'プレミアムガチャ' AND c.rarity >= 3
''')

# 排出表 (確率付き) を見る
run('''
SELECT g.name AS gacha, c.name AS chara, c.rarity, gi.weight,
       round(gi.weight * 100.0 / sum(gi.weight) over (partition by g.id), 2) AS pct
  FROM gacha_items gi
  JOIN gachas g     ON g.id = gi.gacha_id
  JOIN characters c ON c.id = gi.character_id
 ORDER BY g.id, gi.weight DESC
''')
"""),
]

# step4
cells += [
    md("""## Step 4 — `user_characters` (= 履歴 / Box) + トランザクション

ガチャを 1 回引く処理は 「coins -100 / 履歴に1行 INSERT」の 2 つの書き換え。
**両方成功 or 両方失敗** にする必要があります。これがトランザクション。
"""),
    code("""run('''
CREATE TABLE user_characters (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      INTEGER NOT NULL REFERENCES users(id)      ON DELETE CASCADE,
    character_id INTEGER NOT NULL REFERENCES characters(id) ON DELETE RESTRICT,
    obtained_at  TEXT    NOT NULL DEFAULT (datetime('now'))
)
''')
run("CREATE INDEX idx_user_characters_user ON user_characters(user_id)")

# alice が通常ガチャを 1 回引いてスライムが当たった、を SQL で再現
conn.execute("BEGIN")
conn.execute("UPDATE users SET coins = coins - 100 WHERE name = 'alice'")
conn.execute('''
INSERT INTO user_characters (user_id, character_id)
SELECT u.id, c.id FROM users u, characters c
 WHERE u.name = 'alice' AND c.name = 'スライム'
''')
conn.execute("COMMIT")

run("SELECT name, coins FROM users WHERE name = 'alice'")
run('''
SELECT u.name AS user, c.name AS chara, uc.obtained_at
  FROM user_characters uc
  JOIN users      u ON u.id = uc.user_id
  JOIN characters c ON c.id = uc.character_id
 ORDER BY uc.id
''')
"""),
]

# step5
cells += [
    md("""## Step 5 — JOIN + GROUP BY + ウィンドウ関数で Box を出す

ガチャを何回も引いて、所持品 (Box) を SQL 1 本で集計する練習。
"""),
    code("""# alice にあと数回引かせる (ロジックは Step 4 と同じ。今回は色んなキャラに)
import random
random.seed(0)
for chara in ['スライム', 'ウルフ', 'スライム', 'ナイト', 'ウルフ', 'ペガサス', 'スライム']:
    conn.execute("BEGIN")
    conn.execute("UPDATE users SET coins = coins + 100 WHERE name='alice'")  # テスト用 補充
    conn.execute("UPDATE users SET coins = coins - 100 WHERE name='alice'")
    conn.execute('''
        INSERT INTO user_characters (user_id, character_id)
        SELECT u.id, c.id FROM users u, characters c
         WHERE u.name = 'alice' AND c.name = ?
    ''', (chara,))
    conn.execute("COMMIT")

# Box: 所持キャラを個数付きで
print("== alice の Box ==")
run('''
SELECT c.name, c.rarity, c.emoji, COUNT(*) AS count
  FROM user_characters uc
  JOIN characters c ON c.id = uc.character_id
  JOIN users      u ON u.id = uc.user_id
 WHERE u.name = 'alice'
 GROUP BY c.id
 ORDER BY c.rarity DESC, c.id
''')

# 全キャラ + 所持数 (LEFT JOIN: 未所持も含めて出す)
print("\\n== 全キャラ × alice の所持状況 ==")
run('''
SELECT c.name, c.rarity, COUNT(uc.id) AS owned
  FROM characters c
  LEFT JOIN user_characters uc
         ON uc.character_id = c.id
        AND uc.user_id = (SELECT id FROM users WHERE name='alice')
 GROUP BY c.id
 ORDER BY c.rarity DESC, c.id
''')
"""),
    md("""ここまでが第 2 章のキモ。
これで `server/app.py` の `GET /api/box` が発行している SQL がそのまま読めるようになります。
"""),
]


# ============================================================================
# 4. 本物のフルセットコードを書き出す
# ============================================================================
cells += [
    md("""---
# 第 3〜8 章 (圧縮版) — 本物のサーバー一式を書き出す

ここから先 (Postgres / psycopg / 認証 / セッション / ガチャ抽選 / Box / フロント) は、
**完成版コードを `%%writefile` で 一気に書き出して、動かしながら読む** 形で進めます。

各ファイルは「読み物としてもう書いてある」 ので、冒頭の docstring とコメントを
追ってください。コピペした時点でフルセットがそろいます。
"""),
]

cells += [
    md("## `db/schema.sql` — テーブル定義 (PostgreSQL方言)"),
    writefile("db/schema.sql", read("db/schema.sql")),
    md("## `db/seed.sql` — キャラ/ガチャ/排出設定 の初期データ"),
    writefile("db/seed.sql", read("db/seed.sql")),
    md("## `server/__init__.py`"),
    writefile("server/__init__.py", ""),
    md("""## `server/db.py` — DB 接続 (psycopg を使う本番用)

このファイルは PostgreSQL 用です。
あとで Notebook 用の **SQLite 互換アダプタ** をかぶせて切り替えます。
"""),
    writefile("server/db.py", read("server/db.py")),
    md("## `server/auth.py` — パスワードハッシュ + セッション"),
    writefile("server/auth.py", read("server/auth.py")),
    md("## `server/gacha.py` — 重み付き乱択でガチャを 1 回引く"),
    writefile("server/gacha.py", read("server/gacha.py")),
    md("## `server/app.py` — http.server + ルーター + 全 API"),
    writefile("server/app.py", read("server/app.py")),
    md("## `web/index.html` — ガチャ画面 (HTML)"),
    writefile("web/index.html", read("web/index.html")),
    md("## `web/style.css`"),
    writefile("web/style.css", read("web/style.css")),
    md("## `web/app.js` — ブラウザ側ロジック"),
    writefile("web/app.js", read("web/app.js")),
]


# ============================================================================
# 5. SQLite 互換アダプタを差し込む
# ============================================================================
cells += [
    md("""---
# 第 X 章 — Notebook で動かす: SQLite 互換アダプタ

`server/db.py` は psycopg + PostgreSQL 用に書かれているので、
このまま Colab で動かすには Postgres を別途立てる必要があります。

そこで **本番コードに一切手を加えずに**、`server.db.get_conn` だけ
SQLite にしゃべる関数に差し替えるアダプタを用意します。

> 後で本物の Postgres に切り替えたいときは、この差し替えセルを実行**しなければ**
> 元の psycopg ベースに戻ります。 (= 抽象化はここに集約されています)
"""),
    writefile("sqlite_adapter.py", read("tests/sqlite_adapter.py")),
    code("""# 本物の DDL を SQLite 用に変換する小ヘルパ
import re

def translate_pg_to_sqlite(sql: str) -> str:
    sql = re.sub(r"SELECT setval\\([^;]*?\\);", "", sql, flags=re.DOTALL | re.I)
    sql = re.sub(r"\\bBIGSERIAL\\s+PRIMARY KEY\\b",
                 "INTEGER PRIMARY KEY AUTOINCREMENT", sql, flags=re.I)
    sql = re.sub(r"\\bBIGSERIAL\\b", "INTEGER PRIMARY KEY AUTOINCREMENT", sql, flags=re.I)
    sql = re.sub(r"\\bBIGINT\\b",   "INTEGER", sql, flags=re.I)
    sql = re.sub(r"\\bSMALLINT\\b", "INTEGER", sql, flags=re.I)
    sql = re.sub(r"\\bTIMESTAMPTZ\\b", "TIMESTAMP", sql, flags=re.I)
    sql = re.sub(r"\\bDEFAULT NOW\\(\\)", "DEFAULT (datetime('now'))", sql, flags=re.I)
    return sql

schema_pg   = open("db/schema.sql", encoding="utf-8").read()
seed_pg     = open("db/seed.sql",   encoding="utf-8").read()
schema_lite = translate_pg_to_sqlite(schema_pg)
seed_lite   = translate_pg_to_sqlite(seed_pg)
print(schema_lite[:300], "...")
"""),
    code("""# server.db を SQLite 版に差し替える
import importlib, sqlite_adapter, server.db

sqlite_adapter.init_shared_db(schema_lite, seed_lite)
server.db.get_conn = sqlite_adapter.get_conn
server.db.healthcheck = sqlite_adapter.healthcheck

# server.app は import 時に from .db import get_conn しているので、再 import する
import server.app
importlib.reload(server.app)
server.app.get_conn = sqlite_adapter.get_conn

# 接続できるか確認
print("healthcheck:", server.db.healthcheck())
"""),
]


# ============================================================================
# 6. サーバーを起動
# ============================================================================
cells += [
    md("""---
# サーバーを起動 (バックグラウンドスレッド)

`server/app.py` の `GachaHandler` を、Notebook プロセス内のスレッドで起動します。
ポート 8000 で待ち受け、Colab なら `serve_kernel_port_as_public` で外向きに公開します。
"""),
    code("""from http.server import ThreadingHTTPServer
import threading, time

PORT = 8000
_httpd = ThreadingHTTPServer(("0.0.0.0", PORT), server.app.GachaHandler)
_thread = threading.Thread(target=_httpd.serve_forever, daemon=True)
_thread.start()
time.sleep(0.5)
print(f"server listening on :{PORT}")

# Colab なら公開URLを取得 (外向きにする)
try:
    from google.colab import output as _colab_output
    PUBLIC_URL = _colab_output.serve_kernel_port_as_public(PORT)
    if PUBLIC_URL.endswith("/"):
        PUBLIC_URL = PUBLIC_URL[:-1]
    print("public URL:", PUBLIC_URL)
except Exception:
    PUBLIC_URL = f"http://127.0.0.1:{PORT}"
    print("local URL:", PUBLIC_URL)
"""),
]


# ============================================================================
# 7. API を叩いてみる
# ============================================================================
cells += [
    md("""---
# API を叩いてみる

`requests` を使って (Colab に標準で入っています)、ユーザー登録 → ガチャ → Box 確認 まで通します。
出力を見ながら、 「これは `server/app.py` のどのハンドラに対応しているのか?」 を
照らし合わせながら進めると吸収が速いです。
"""),
    code("""import requests, json, random

s = requests.Session()
USER = f"colab_user_{random.randint(1000, 9999)}"
PWD  = "secret123"

# 1. 登録
r = s.post(PUBLIC_URL + "/api/register",
           json={"name": USER, "password": PWD, "display_name": "コラボ太郎"})
print("register:", r.status_code, r.json())

# 2. /api/me で自分の情報を確認
print("me      :", s.get(PUBLIC_URL + "/api/me").json())

# 3. ガチャ一覧
print("gachas  :", s.get(PUBLIC_URL + "/api/gacha/list").json())

# 4. 通常ガチャを 5 連
print("\\n=== 5連ガチャ ===")
for i in range(5):
    r = s.post(PUBLIC_URL + "/api/gacha/pull", json={"gacha_id": 1}).json()
    c = r["character"]
    stars = "★" * c["rarity"] + "☆" * (5 - c["rarity"])
    print(f"  {i+1}. {c['emoji']} {c['name']:8s} {stars}  残コイン: {r['coins']}")

# 5. Box (集計済み)
print("\\n=== Box ===")
box = s.get(PUBLIC_URL + "/api/box").json()
for it in box["items"]:
    stars = "★" * it["rarity"]
    print(f"  ×{it['count']:2d}  {it['emoji']}  {it['name']:8s}  {stars}")
print(f"通算 {box['total_pulls']} 回, {len(box['items'])} 種類")
"""),
]


# ============================================================================
# 8. ブラウザで遊ぶ (Notebook内に表示)
# ============================================================================
cells += [
    md("""---
# Notebook 内でガチャ画面を表示する

`web/index.html` + `web/style.css` + `web/app.js` を 1 枚の HTML に組み立てて、
`IPython.display.HTML` で表示します。
**API のベース URL を Colab 用の公開 URL に書き換える** のがミソ。
"""),
    code("""from IPython.display import HTML, display

html_src = open("web/index.html", encoding="utf-8").read()
css_src  = open("web/style.css", encoding="utf-8").read()
js_src   = open("web/app.js",    encoding="utf-8").read()

# index.html は <link rel="stylesheet" href="./style.css"> と <script src="./app.js" type="module">
# を使っているが、Notebook 内では取れないのでインライン化する
html_src = html_src.replace(
    '<link rel="stylesheet" href="./style.css">',
    f'<style>{css_src}</style>')
html_src = html_src.replace(
    '<script src="./app.js" type="module"></script>',
    f'<script type="module">{js_src}</script>')

# API_BASE をこのセッションの公開 URL に差し替える
html_src = html_src.replace(
    'const API_BASE = "http://localhost:8000";',
    f'const API_BASE = "{PUBLIC_URL}";')

display(HTML(html_src))
"""),
    md("""**🎉 上のセルの直下に、ガチャ画面が出現します。**

操作の流れ:
1. 上のセクションで作ったユーザー (例: `colab_user_1234` / `secret123`) でログイン、または別途登録
2. 「引く」ボタンでガチャを引く。レア度に応じて演出が変わる
3. 下の「Box」に獲得済みキャラが個数付きで蓄積される

> Notebook の中で動いているので、**サーバーを止めるとこの画面も止まります**。
> 上の方のセルの `_httpd` を `_httpd.shutdown()` で停止できます。
"""),
]


# ============================================================================
# 9. 残り章 + 拡張へ
# ============================================================================
cells += [
    md("""---
# ここから先 — 拡張章の道しるべ

ここまでで「動くガチャシステム」が手元に揃いました。
`server/`, `db/`, `web/` の中身は本物のフルセット。 リポジトリ直下のものと同じです。

## 第 3 章 (本格版) — PostgreSQL を Docker で動かす

Notebook で SQLite を使ってきましたが、本番想定は PostgreSQL です。
**コードは一切変えずに**、リポジトリの `docker-compose.yml` を起動して
`server.db.get_conn` の差し替えセルを **実行しないだけ** で本物の PG に切り替わります。

ローカルで:
```bash
docker compose up -d                                # PG が立ち上がる
pip install -r server/requirements.txt              # psycopg 入れる
python -m server.app                                # 本物起動
python -m http.server 5500 --directory web         # フロント配信
```

## 第 4 章 — psycopg

Notebook が使った `sqlite_adapter` と本物の `server/db.py` を見比べてください。
カーソル → 行 → コミット という流れは同じ。違いは「TCP 越しに PG にしゃべる」ことだけ。

## 第 5〜8 章 — 認証 / 抽選 / Box / セッション

それぞれ `server/auth.py`, `server/gacha.py`, `server/app.py` の各ハンドラを
ゆっくり読み直すのが宿題です。 docstring とインラインコメントが「本文」 になっています。

## 第 9 章 — 拡張: クッキークリッカー化

ガチャを軸にゲームを膨らませる方向の話 (ログインボーナス、装備、レベル、リアルタイム…)。
リポジトリの `docs/ch09-extending.html` に骨子があります。

## テスト

```bash
python tests/test_unit.py        # auth + gacha のユニットテスト
python tests/test_e2e_sqlite.py  # SQLite で API を E2E 検証 (27 ケース)
bash  tests/smoke_curl.sh        # 本物の PG + サーバー相手の curl 通し
```
"""),
    md("""---
## まとめ

- HTTP は「テキストの往復」 — 6 ステップでフレームワーク無しで書けた
- DB は「整合性を強制してくれる表の集まり」 — 中間テーブルとトランザクションが武器
- Python から DB を触るのは「カーソル → 行 → コミット」 — psycopg も sqlite3 も骨格は同じ
- 認証はハッシュ + ソルト + 反復、セッションは Cookie でトークンを送るだけ
- ガチャ抽選は重み付き乱択 = 累積和 + 二分探索が古典実装、`random.choices` でも書ける
- 完走おつかれさま 🎉
"""),
]


# ===========================================================================
# Assemble
# ===========================================================================
notebook = {
    "cells": cells,
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3",
        },
        "language_info": {"name": "python"},
        "colab": {"provenance": [], "toc_visible": True},
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}

NB_PATH.write_text(json.dumps(notebook, ensure_ascii=False, indent=1),
                    encoding="utf-8")
print(f"wrote {NB_PATH}  ({len(cells)} cells)")
