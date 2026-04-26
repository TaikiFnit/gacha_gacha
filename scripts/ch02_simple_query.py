"""第2章 / 練習2: 通常ガチャの排出キャラを確率付きで出す。

実行:
    python scripts/ch02_simple_query.py

期待される出力 (確率は seed.sql の weight に依存):
    通常ガチャ (id=1) の排出表
       19.80%  スライム      ★☆☆☆☆ 🟢
       19.80%  コウモリ      ★☆☆☆☆ 🦇
       ...
        0.20%  伝説の勇者    ★★★★★ ⚔️

意図:
    ・JOIN: gachas / gacha_items / characters を 1 枚にする
    ・ウィンドウ関数 SUM(weight) OVER () で「全体の合計」を 1 行ごとに引っ張れる
    ・ORDER BY: 表示順を決める
"""
# プロジェクト直下から `python scripts/...` 形式で起動できるように import パスを通す
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from server.db import get_conn  # noqa: E402

GACHA_ID = 1


def main() -> None:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT c.name,
                   c.rarity,
                   c.emoji,
                   gi.weight,
                   gi.weight * 100.0 / SUM(gi.weight) OVER () AS pct
              FROM gacha_items gi
              JOIN characters c ON c.id = gi.character_id
             WHERE gi.gacha_id = %s
             ORDER BY gi.weight DESC, c.id
            """,
            (GACHA_ID,),
        )
        rows = cur.fetchall()

        print(f"通常ガチャ (id={GACHA_ID}) の排出表")
        for r in rows:
            stars = "★" * r["rarity"] + "☆" * (5 - r["rarity"])
            print(f"  {float(r['pct']):6.2f}%  {r['name']:8s} {stars} {r['emoji']}")


if __name__ == "__main__":
    main()
