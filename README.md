# gacha_gacha — データベース学習用ガチャシステム

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/taikifnit/gacha_gacha/blob/master/gacha_gacha.ipynb)

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
- 全章のコピペ済みノートブック (答え): `gacha_gacha.ipynb`
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
│   ├── ch01-http.html
│   ├── ch02-database.html
│   ├── ch03-postgres-docker.html
│   ├── ch04-psycopg.html
│   ├── ch05-auth.html
│   ├── ch06-gacha-algorithm.html
│   ├── ch07-box-and-join.html
│   ├── ch08-session.html
│   ├── ch09-extending.html
│   └── assets/
│       ├── style.css
│       └── prism.css        ← コードハイライト
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

# 4. API サーバーを起動 (http://localhost:8000)
python -m server.app

# 5. 別ターミナルでフロントを配信 (http://localhost:5500)
python -m http.server 5500 --directory web

# 6. ブラウザで http://localhost:5500 を開く
```

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

このリポジトリを GitHub に公開して、`Open in Colab` バッジから直接 Colab に
ノートブックを開けるようにする手順:

```bash
# 1. https://github.com/new で空のリポジトリを作成
#    名前は taikifnit/gacha_gacha (README/.gitignore は付けない)

# 2. ローカルから push
git remote add origin git@github.com:taikifnit/gacha_gacha.git
git branch -M master                  # main にしたければ -M main
git push -u origin master

# 3. (任意) GitHub Pages で docs/ を公開
#    Settings → Pages → Source: Deploy from a branch
#    Branch: master / Folder: /docs
```

公開後、 `Open in Colab` バッジは
`https://colab.research.google.com/github/<user>/<repo>/blob/<branch>/gacha_gacha.ipynb`
で開きます。 リポジトリ名やユーザー名を変えた場合は `README.md` と `docs/index.html` の URL を一緒に書き換えてください。

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

| 章   | テーマ                                | ステータス     |
| ---- | ------------------------------------- | -------------- |
| Ch.0 | 全体像と学び方                         | ✅ 本文あり    |
| Ch.1 | HTTP サーバーを建ててみよう            | ✅ 本文あり    |
| Ch.2 | データベース基礎とテーブル設計         | ✅ 本文あり    |
| Ch.3 | PostgreSQL を Docker で動かす          | 🚧 骨子        |
| Ch.4 | Python から DB を触る (psycopg 入門)  | 🚧 骨子        |
| Ch.5 | パスワードハッシュとユーザー登録       | 🚧 骨子        |
| Ch.6 | ガチャ抽選アルゴリズム (重み付き乱択) | 🚧 骨子        |
| Ch.7 | Box と JOIN・集計                     | 🚧 骨子        |
| Ch.8 | セッションと簡易認証                   | 🚧 骨子        |
| Ch.9 | 拡張: クッキークリッカー化への道       | 🚧 骨子        |

「骨子」はゴールと参照コードだけ書いてあります。あとから自分で本文を書き足していくのが
理想的な学習の続き方です。

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
