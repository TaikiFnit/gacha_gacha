"""第16章 / 練習: API 互換性 smoke (本物のサーバ向け)。

exercises/ch16/step6_api_smoke.py と中身は同じ。 scripts/ にも置くことで、
普段の作業フォルダから直接実行しやすくしてある。

実行:
    python -m server.app  # 別ターミナル
    python scripts/ch16_api_smoke.py
"""
import os
import sys

sys.path.insert(
    0,
    os.path.join(os.path.dirname(__file__), "..", "exercises", "ch16"),
)
from step6_api_smoke import main   # noqa: E402

if __name__ == "__main__":
    main()
