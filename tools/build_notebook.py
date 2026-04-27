"""DEPRECATED — このスクリプトは廃止されました。

教材は docs/ 配下の HTML が source of truth です。
ノートブックは廃止し、 必要になった時点で再構築する方針です。

削除手順 (リポジトリ管理者向け):
    git rm gacha_gacha.ipynb tools/build_notebook.py
    git commit -m 'remove deprecated notebook'
"""

if __name__ == "__main__":
    raise SystemExit(
        "このスクリプトは廃止されました。 docs/ 配下の HTML を参照してください。"
    )
