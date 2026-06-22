"""アプリ設定 (環境変数から読み込む).

環境変数:
    AW_DB_PATH     SQLite データベースのパス (デフォルト: automatic_waddle.db)
    AW_VAULT_PATH  Obsidian vault のパス (未設定なら Obsidian 連携は無効)
"""

from __future__ import annotations

import os
from typing import Optional

from app.storage import DEFAULT_DB_PATH


def get_db_path() -> str:
    return os.environ.get("AW_DB_PATH", DEFAULT_DB_PATH)


def get_vault_path() -> Optional[str]:
    return os.environ.get("AW_VAULT_PATH") or None
