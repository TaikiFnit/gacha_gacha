# gacha_gacha — データベース学習用ガチャシステム

このリポジトリは「自分の手でバックエンドを建てて、データベースの基礎を体で覚える」ための
学習プロジェクトです。Web ブラウザで動くごく小さなガチャゲームを題材に、

- HTTP サーバーが受け付けるリクエストの中身
- SQL とテーブル設計 (SQLite で導入 → PostgreSQL で本番想定)
- Python から DB を触る感触
- ガチャ抽選ロジック (重み付き乱択) の実装

を、フレームワークの魔法に頼らず、**ほぼ Python 標準ライブラリと生SQL** だけで作ってあります。

## まず最初に — 教材を開く

教材は **[docs/index.html](docs/index.html)** から始まります。Google Colab を開きながら、
各章の指示通りに「新しいセルにコピペ → Shift+Enter」 を繰り返すだけで進みます。

- 教材 (HTML, GitHub Pages 配信予定): `docs/index.html`
- 本物のサーバー一式 (本番想定): `server/`, `db/`, `web/`

> ⚠️ プロダクション用ではありません。学習目的で読みやすさを最優先にしています。
> パスワード保護やセッション管理も「最低限の安全」レベルにとどめています。

---

## ディレクトリ構成

```
gacha_gacha/
├── README.md                ← いま読んでいるファイル
├── docker-compose.yml       ← PostgreSQL を Docker で起動するための定義
├── .env.example             ← 環境変数のサンプル (DB接続情報)
├── db/
│   ├── schema.sql           ← テーブル定義 (DDL)
│   └── seed.sql             ← 初期データ (キャラクター, ガチャ筐体, 排出設定)
├── server/
│   ├── app.py               ← http.server を使った API サーバー本体
│   ├── db.py                ← psycopg を使った薄い DB ラッパー
│   ├── auth.py              ← パスワードハッシュ + セッション
│   ├── gacha.py             ← ガチャ抽選アルゴリズム
│   └── requirements.txt     ← Python の依存 (psycopg だけ)
├── web/                     ← ガチャを引く側のフロント (静的HTML/JS)
│   ├── index.html
│   ├── app.js
│   └── style.css
├── docs/                    ← 教材サイト (ローカルで開ける静的Web)
│   ├── index.html           ← 目次
│   ├── ch00-overview.html
│   ├── ch01-http.html       ← HTTP サーバー
│   ├── ch02-database.html   ← DB の基礎
│   ├── ch03-connect.html    ← サーバ × DB を連結
│   ├── ch04-postgres-docker.html ← フロント連携 + CORS
│   ├── ch05-gacha.html      ← ガチャ抽選 + トランザクション
│   ├── ch06-box.html        ← Box (JOIN + GROUP BY)
│   ├── ch07-auth.html       ← ユーザー管理 (Bearer Token)
│   ├── ch08-local.html      ← Postgres + Docker + 仕上げ
│   ├── ch09-extending.html  ← 拡張アイディア集
│   ├── api-spec.html        ← API 仕様書
│   └── assets/
│       ├── style.css
│       ├── copy-button.js
│       ├── inject-toc.js
│       ├── toc.html         ← 共通サイドバー
│       └── figs/            ← 図版 (リレーション / JOIN / GROUP BY / 重み付き乱択)
├── exercises/               ← ステップ式実習 (各章でこれを自分で書く)
│   ├── ch01/                ← step1〜6 を順に解いて HTTP サーバーを組み上げる
│   └── ch02/                ← step1〜6 を順に解いて DB スキーマを組み上げる
├── tests/                   ← 動作保証
│   ├── test_unit.py                ← 認証ハッシュ + ガチャ抽選分布 (DB不要)
│   ├── test_e2e_sqlite.py          ← SQLite で全 API を E2E 検証
│   ├── sqlite_adapter.py           ← psycopg API 互換 SQLite ラッパ
│   ├── translate_schema.py         ← schema.sql を SQLite 用に変換
│   └── smoke_curl.sh               ← 本物の Postgres + サーバーに curl 一気通貫
└── scripts/                 ← 補助スクリプト (DB探索など)
    ├── ch01_hello_http.py
    ├── ch01_post_json.py
    ├── ch02_explore_schema.py
    └── ch02_simple_query.py
```

---

## クイックスタート

前提: Docker / Docker Compose と Python 3.10+ が入っていること。

```bash
# 1. PostgreSQL を立てる (バックグラウンド)
docker compose up -d

# 2. Python の依存をインストール
python -m venv .venv
source .venv/bin/activate     # Windows は .venv\Scripts\activate
pip install -r server/requirements.txt

# 3. 環境変数を読み込み (任意。既定値で動く想定)
cp .env.example .env
# .env を実際にプロセスに読み込ませたい場合は、 起動前にこれを実行:
#   set -a; source .env; set +a
# (このリポジトリのコードは python-dotenv に依存していないため、
#  .env ファイルを置くだけでは反映されません。 上の `source` で
#  シェル変数として読み込ませます)

# 4. API サーバーを起動 (http://localhost:8000)
python -m server.app

# 5. 別ターミナルでフロントを配信 (http://localhost:5500)
python -m http.server 5500 --directory web

# 6. ブラウザで http://localhost:5500 を開く
```

### DB を最初からやり直したい場合

```bash
# Docker ボリュームごと消して、 schema.sql + seed.sql を再投入
docker compose down -v
docker compose up -d
```

`db/seed.sql` はキャラクターやガチャ筐体の ID を手で振っているので、
中途半端に追加投入するより `down -v` で完全に作り直すのが確実です。

### テストを動かして確認

```bash
# DB 不要のユニットテスト (認証 / 抽選アルゴリズム)
python tests/test_unit.py

# SQLite ベースの E2E テスト (Docker 不要、PostgreSQL 不要)
# server/app.py を本物として起動し、全 API を順に叩いて検証する
python tests/test_e2e_sqlite.py

# 本物の Postgres + サーバーで E2E を確認したいとき
docker compose up -d
python -m server.app &           # 別ターミナル推奨
bash tests/smoke_curl.sh
```

期待する出力 (`test_e2e_sqlite.py`):
```
========== summary ==========
  27 passed, 0 failed, 27 total
```

### 教材サイト

教材サイトは `docs/index.html` をブラウザで直接開くだけで読めます。

---

## GitHub に公開する

```bash
# 1. https://github.com/new で空のリポジトリを作成
#    名前は taikifnit/gacha_gacha (README/.gitignore は付けない)

# 2. ローカルから push
git remote add origin git@github.com:taikifnit/gacha_gacha.git
git branch -M main
git push -u origin main

# 3. (任意) GitHub Pages で docs/ を公開
#    Settings → Pages → Source: Deploy from a branch
#    Branch: main / Folder: /docs
```

リポジトリ名やユーザー名を変えた場合は `README.md` の URL を書き換えてください。

```bash
# 一括置換するなら
grep -rl "taikifnit/gacha_gacha" . --include='*.md' --include='*.html' \
  | xargs sed -i '' 's|taikifnit/gacha_gacha|<NEW_USER>/<NEW_REPO>|g'
```

```bash
# 教材も http で配信したい場合
python -m http.server 5501 --directory docs
# → http://localhost:5501
```

---

## 学習の進め方

教材は `docs/` の中にあります。
順番に読んで、対応するコード (`server/`, `db/`, `scripts/`) を実際に書き換えながら進めてください。

| 章   | テーマ                                                       | ステータス  |
| ---- | ------------------------------------------------------------ | ----------- |
| Ch.0 | 全体像 + Colab セットアップ                                   | ✅ 本文あり |
| Ch.1 | HTTPサーバーを段階的に組み立てる (Colab、6 ステップ)                     | ✅ 本文あり |
| Ch.2 | データベース基礎 (1 テーブルから)                             | ✅ 本文あり |
| Ch.3 | サーバとデータベース連結 — 最初に動くものを作る                             | ✅ 本文あり |
| Ch.4 | フロントを足してガチャ画面を呼ぶ                              | ✅ 本文あり |
| Ch.5 | ガチャ抽選を本実装 (single user、 トランザクション)            | ✅ 本文あり |
| Ch.6 | Box と JOIN・集計 (single user)                              | ✅ 本文あり |
| Ch.7 | ユーザー管理を導入 (auth、 「個別 Box」 への動機付き)          | ✅ 本文あり |
| Ch.8 | ローカル移行 + 仕上げ (Postgres + Docker + 分割 + テスト)      | ✅ 本文あり |
| Ch.9 | 拡張アイディア集                                              | ✅ 本文あり |

「骨子」はゴールと参照コードだけ書いてあります。あとから自分で本文を書き足していくのが
理想的な学習の続き方です。

### 教材 (docs/) と実習 (exercises/) の対応

`docs/` の各章は Colab + コピペで進める「読みながら動かす」形式の本編です。
一方 `exercises/` は手元の Python プロセスやローカル PostgreSQL に対して
書き起こす型の実習で、 章ごとにステップ式で並んでいます。

| 教材 (docs/)               | 対応する実習 (exercises/) | 備考                                       |
| -------------------------- | ------------------------ | ------------------------------------------ |
| `ch01-http.html`           | `exercises/ch01/`        | step1〜6 を順に解いて HTTP サーバーを組み上げる |
| `ch02-database.html`       | `exercises/ch02/`        | step1〜6 を順に解いて DB スキーマを組み上げる   |
| `ch03-connect.html` 以降    | (実習未整備)              | docs のコピペセルで完結                       |

Ch.3 以降の実習は今後の追加候補です。 現状の本編コードは
`server/` `db/` `web/` `tests/` に「最終形」 が置かれているので、
docs を読みながら自分で写経 → そこと差分を取って答え合わせ、 という進め方ができます。

---

## 動作確認用 API 早見表

| メソッド | パス                | 機能                       | 認証 |
| -------- | ------------------- | -------------------------- | ---- |
| POST     | `/api/register`     | ユーザー登録               | -    |
| POST     | `/api/login`        | ログイン (セッション発行)  | -    |
| POST     | `/api/logout`       | ログアウト                 | 必要 |
| GET      | `/api/me`           | 自分の情報                 | 必要 |
| GET      | `/api/gacha/list`   | ガチャ筐体の一覧            | -    |
| POST     | `/api/gacha/pull`   | ガチャを 1 回引く           | 必要 |
| GET      | `/api/box`          | 自分の所持キャラ一覧        | 必要 |

詳細は `server/app.py` を読んでください。学習用なので、
ロジックを追えば全部追える短さに留めています。
