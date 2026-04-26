"""ガチャ抽選ロジック。

ここがゲームバックエンドで一番面白い部分。
gacha_items テーブルから (character_id, weight) を引いてきて、
weight の合計を分母にした重み付き乱択を行う。

- 単純実装: weight をリストにして bisect/random.choices で 1 個選ぶ
- DB 一発で抽選するパターンも紹介可能 (ORDER BY -log(random())/weight LIMIT 1)
  → 学習として両方のやり方に触れたいので、Pythonでやるバージョンと
    SQLだけでやるバージョンを Ch.6 で比較する。

このモジュールは "Pythonで重み付き乱択" のシンプルな実装。
"""

from __future__ import annotations

import random
from dataclasses import dataclass

import psycopg


@dataclass
class GachaItem:
    character_id: int
    name: str
    rarity: int
    emoji: str
    weight: int


def fetch_pool(conn: psycopg.Connection, gacha_id: int) -> list[GachaItem]:
    """指定ガチャの排出プールを (character情報 + weight) で取ってくる。"""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT c.id   AS character_id,
                   c.name,
                   c.rarity,
                   c.emoji,
                   gi.weight
              FROM gacha_items gi
              JOIN characters c ON c.id = gi.character_id
             WHERE gi.gacha_id = %s
             ORDER BY c.rarity, c.id
            """,
            (gacha_id,),
        )
        rows = cur.fetchall()
    return [GachaItem(**r) for r in rows]


def draw(pool: list[GachaItem], rng: random.Random | None = None) -> GachaItem:
    """重み付き乱択を 1 回行う。

    実装は random.choices に任せている。
    手で書くなら:

        total = sum(item.weight for item in pool)
        r = rng.uniform(0, total)
        acc = 0
        for item in pool:
            acc += item.weight
            if r <= acc:
                return item

    という累積和の二分探索パターンを書くことになる。Ch.6 で詳しく解説する。
    """
    if not pool:
        raise ValueError("ガチャに排出設定が 1 件もありません")
    rng = rng or random.SystemRandom()  # 暗号学的乱数で
    weights = [item.weight for item in pool]
    return rng.choices(pool, weights=weights, k=1)[0]
