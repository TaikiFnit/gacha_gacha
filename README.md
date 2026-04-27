# gacha_gacha — データベース学習用ガチャシステム

このリポジトリは「自分の手でバックエンドを建てて、 データベースの基礎を体で覚える」 ための
学習プロジェクトです。 Web ブラウザで動くごく小さなガチャゲームを題材に、

- HTTP サーバーが受け付けるリクエストの中身
- SQL とテーブル設計 (PostgreSQL を Docker で立てる)
- Python から DB を触る感触 (psycopg)
- ガチャ抽選ロジック (重み付き乱択) の実装

を、 フレームワークの魔法に頼らず、 **ほぼ Python 標準ライブラリ + psycopg + 生 SQL** だけで作ってあります。

## まず最初に — 教材を開く

教材は **[docs/index.html](docs/index.html)** から始まります。 Windows PC のローカルで
Python と Docker Desktop と Bruno を動かしながら、 各章の手順通りに「コードを書く →
PowerShell で動かす → Bruno で叩く」 を繰り返すだけで進みます。

- 教材 (HTML, GitHub Pages 配信予定): `docs/index.html`
- 本物のサーバー一式 (本番想定): `server/`, `db/`, `web/`

> ⚠️ プロダクション用ではありません。 学習目的で読みやすさを最優先にしています。
> パスワード保護やセッション管理も「最低限の安全」 レベルにとどめています。

---

## ディレクトリ構成

```
gacha_gacha/
├── README.md                ← いま読んでいるファイル
├── LICENSE                  ← MIT
├── .gitattributes           ← 改行コード設定 (CRLF/LF 対策)
├── .editorconfig            ← エディタ間で字下げ等を揃える
├── .env.example             ← 環境変数のサンプル (DB接続情報)
├── docker-compose.yml       ← PostgreSQL を Docker で起動するための定義
├── db/
│   ├── schema.sql           ← テーブル定義 (DDL)
│   └── seed.sql             ← 初期データ (キャラクター, ガチャ筐体, 排出設定)
├── server/                  ← API サーバー本体 (Ch.8 で分割した完成版)
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
│   ├── ch00-overview.html   ← 全体像 + Windows 環境構築
│   ├── ch01-http.html       ← HTTP サーバーを段階的に組み立てる
│   ├── ch02-database.html   ← Postgres + Docker でデータベース基礎
│   ├── ch03-connect.html    ← Python から DB を叩く (psycopg)
│   ├── ch04-postgres-docker.html ← フロント連携 + CORS
│   ├── ch05-gacha.html      ← ガチャ抽選 + トランザクション
│   ├── ch06-box.html        ← Box (JOIN + GROUP BY)
│   ├── ch07-auth.html       ← ユーザー管理 (Bearer Token)
│   ├── ch08-local.html      ← ファイル分割 + .env + 自動テスト
│   ├── ch09-extending.html  ← 拡張アイディア集
│   ├── api-spec.html        ← API 仕様書
│   └── assets/
│       ├── style.css
│       ├── copy-button.js
│       ├── inject-toc.js
│       ├── toc.html         ← 共通サイドバー
│       └── figs/            ← 図版 (リレーション / JOIN / GROUP BY / 重み付き乱択)
├── exercises/               ← (一部) ステップ式実習
│   ├── ch01/                ← Ch.1 の各ステップのスナップショット (step1〜6)
│   └── ch02/                ← Ch.2 関連の playground 用 SQL
├── tests/                   ← 動作保証
│   ├── test_unit.py                ← 認証ハッシュ + ガチャ抽選分布 (DB不要)
│   ├── test_e2e_sqlite.py          ← SQLite で全 API を E2E 検証 (開発者向け)
│   ├── sqlite_adapter.py           ← psycopg API 互換 SQLite ラッパ
│   ├── translate_schema.py         ← schema.sql を SQLite 用に変換
│   └── smoke_curl.sh               ← 本物の Postgres + サーバーに curl 一気通貫
├── scripts/                 ← 補助スクリプト (DB探索など)
│   ├── ch01_hello_http.py
│   ├── ch01_post_json.py
│   ├── ch02_explore_schema.py
│   └── ch02_simple_query.py
└── .github/workflows/test.yml  ← CI: push/PR で unit + e2e 自動実行
```

---

## クイックスタート (Windows ローカル)

前提: Ch.0 で Python 3.11+ / Docker Desktop / Bruno をインストール済み。

PowerShell で:

```powershell
# 1. リポジトリを clone
cd $HOME
git clone https://github.com/taikifnit/gacha_gacha.git
cd gacha_gacha

# 2. PostgreSQL コンテナを起動
docker compose up -d

# 3. Python 仮想環境 + 依存
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r server/requirements.txt

# 4. (任意) 環境変数を読み込み
Copy-Item .env.example .env
Get-Content .env | Where-Object { $_ -and $_ -notmatch '^\s*#' } | ForEach-Object {
    $name, $value = $_ -split '=', 2
    [Environment]::SetEnvironmentVariable($name.Trim(), $value.Trim(), "Process")
}

# 5. API サーバーを起動 (http://localhost:8000)
python -m server.app

# 6. 別 PowerShell でフロントを配信 (http://localhost:5500)
python -m http.server 5500 --directory web

# 7. ブラウザで http://localhost:5500 を開く
```

### DB を最初からやり直したい場合

```powershell
# Docker ボリュームごと消して、 schema.sql + seed.sql を再投入
docker compose down -v
docker compose up -d
```

`db/seed.sql` はキャラクターやガチャ筐体の ID を手で振っているので、
中途半端に追加投入するより `down -v` で完全に作り直すのが確実です。

### テストを動かして確認

```powershell
# DB 不要のユニットテスト (認証 / 抽選アルゴリズム)
python tests\test_unit.py

# SQLite ベースの E2E テスト (Docker 不要、 PostgreSQL 不要)
# server/app.py を本物として起動し、 全 API を順に叩いて検証する (開発者向け)
python tests\test_e2e_sqlite.py
```

期待する出力 (`test_e2e_sqlite.py`):
```
========== summary ==========
  29 passed, 0 failed, 29 total
```

本物の Postgres + サーバーで E2E を確認したいときは Git Bash か WSL から:
```bash
docker compose up -d
python -m server.app &           # 別ターミナル推奨
bash tests/smoke_curl.sh
```

### 教材サイト

教材サイトは `docs/index.html` をローカルの HTTP サーバ経由で開いてください
(`fetch()` を使っているため `file://` だと一部機能が動きません):

```powershell
python -m http.server 5501 --directory docs
# → http://localhost:5501
```

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

---

## 学習の進め方

教材は `docs/` の中にあります。
順番に読んで、 対応するコード (`server/`, `db/`, `scripts/`) を実際に書き換えながら進めてください。

| 章   | テーマ                                                       | ステータス  |
| ---- | ------------------------------------------------------------ | ----------- |
| Ch.0 | 全体像 + Windows 環境構築                                    | ✅ 本文あり |
| Ch.1 | HTTPサーバーを段階的に組み立てる (myserver.py、 6 ステップ)   | ✅ 本文あり |
| Ch.2 | Postgres + Docker でデータベース基礎 (psql で 1 テーブル)     | ✅ 本文あり |
| Ch.3 | Python から DB を叩く (psycopg、 Bruno で叩く)                | ✅ 本文あり |
| Ch.4 | フロントを足してガチャ画面を呼ぶ (CORS)                       | ✅ 本文あり |
| Ch.5 | ガチャ抽選を本実装 (single user、 トランザクション)            | ✅ 本文あり |
| Ch.6 | Box と JOIN・集計 (single user)                              | ✅ 本文あり |
| Ch.7 | ユーザー管理を導入 (auth、 「個別 Box」 への動機付き)          | ✅ 本文あり |
| Ch.8 | 仕上げ + 自動テスト (ファイル分割 + .env + ユニット/CI)        | ✅ 本文あり |
| Ch.9 | 拡張アイディア集                                              | ✅ 本文あり |

### 教材 (docs/) と実習 (exercises/) の対応

`docs/` の各章は手元の Windows PC で進める「読みながら動かす」 形式の本編です。
一方 `exercises/` は章ごとのスナップショットコードや playground 用 SQL を置いてある参照用です。

| 教材 (docs/)               | 対応する実習 (exercises/) | 備考                                           |
| -------------------------- | ------------------------ | ---------------------------------------------- |
| `ch01-http.html`           | `exercises/ch01/`        | step1〜6 の myserver.py スナップショット        |
| `ch02-database.html`       | `exercises/ch02/`        | playground DB 用の SQL ステップ集               |
| `ch03-connect.html` 以降   | (実習未整備)              | docs を読みながら自分で書くスタイル              |

Ch.3 以降の実習は今後の追加候補です。 現状の本編コードは
`server/` `db/` `web/` `tests/` に「最終形」 が置かれているので、
docs を読みながら自分で写経 → そこと差分を取って答え合わせ、 という進め方ができます。

---

## 動作確認用 API 早見表

| メソッド | パス                | 機能                       | 認証 |
| -------- | ------------------- | -------------------------- | ---- |
| POST     | `/api/register`     | ユーザー登録               | -    |
| POST     | `/api/login`        | ログイン (Bearer Token 発行) | -    |
| POST     | `/api/logout`       | ログアウト                 | 必要 |
| GET      | `/api/me`           | 自分の情報                 | 必要 |
| GET      | `/api/gacha/list`   | ガチャ筐体の一覧            | -    |
| POST     | `/api/gacha/pull`   | ガチャを 1 回引く           | 必要 |
| GET      | `/api/box`          | 自分の所持キャラ一覧        | 必要 |

詳細は `server/app.py` を読んでください。 学習用なので、
ロジックを追えば全部追える短さに留めています。

---

## ライセンス

[MIT License](LICENSE) 。 教材本文 / コード / 図版すべて自由に利用・改変できます。
