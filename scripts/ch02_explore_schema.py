"""第2章 / 練習1: スキーマを見て、各テーブルの行数を出す。

実行 (Postgres を起動済みで):
    docker compose up -d
    pip install -r server/requirements.txt
    python scripts/ch02_explore_schema.py

期待される出力:
    schema 'public' のテーブル一覧:
      characters       12 行
      gacha_items      19 行
      gachas            2 行
      sessions          0 行
      user_characters   0 行
      users             0 行

意図:
    information_schema というメタ情報用ビューから、
    自分の DB に何のテーブルがあるか聞く感覚を味わう。
    (どんな RDB でも information_schema は標準的に存在する)
"""
# プロジェクト直下から `python scripts/...` 形式で起動できるように import パスを通す
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from server.db import get_conn  # noqa: E402


def main() -> None:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT table_name
              FROM information_schema.tables
             WHERE table_schema = 'public'
             ORDER BY table_name
            """
        )
        tables = [row["table_name"] for row in cur.fetchall()]

        print("schema 'public' のテーブル一覧:")
        for t in tables:
            # 動的にテーブル名を SQL に埋めるときは psycopg.sql.Identifier を使うのが安全。
            # information_schema から取った値なのでまず安心だが、念のため作法に従う。
            from psycopg import sql
            cur.execute(sql.SQL("SELECT COUNT(*) AS n FROM {}")
                          .format(sql.Identifier(t)))
            n = cur.fetchone()["n"]
            print(f"  {t:18s} {n:>6} 行")


if __name__ == "__main__":
    main()
