"""SQLite による永続化ストレージ.

ワークフロー定義と実行結果 (run) を SQLite に保存する。サーバーを再起動しても
データが残るよう、定義は JSON 文字列としてテーブルに格納する。
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, List, Optional

from app.models import RunResult, Workflow

DEFAULT_DB_PATH = "automatic_waddle.db"


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class Storage:
    """ワークフロー定義と実行結果を SQLite に永続化するストア."""

    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path
        # ":memory:" 以外はディレクトリを用意
        if db_path != ":memory:":
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        # check_same_thread=False で FastAPI のスレッドプールから利用可能にする
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        with self._tx() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS workflows (
                    name        TEXT PRIMARY KEY,
                    definition  TEXT NOT NULL,
                    created_at  TEXT NOT NULL,
                    updated_at  TEXT NOT NULL
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS runs (
                    id             TEXT PRIMARY KEY,
                    workflow_name  TEXT,
                    status         TEXT NOT NULL,
                    final_node     TEXT,
                    result         TEXT NOT NULL,
                    created_at     TEXT NOT NULL
                )
                """
            )

    @contextmanager
    def _tx(self) -> Iterator[sqlite3.Cursor]:
        cur = self._conn.cursor()
        try:
            yield cur
            self._conn.commit()
        except Exception:
            self._conn.rollback()
            raise
        finally:
            cur.close()

    def close(self) -> None:
        self._conn.close()

    # --- workflows ---------------------------------------------------------

    def save_workflow(self, workflow: Workflow) -> None:
        now = _utcnow()
        payload = workflow.model_dump_json()
        with self._tx() as cur:
            cur.execute(
                """
                INSERT INTO workflows (name, definition, created_at, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET
                    definition = excluded.definition,
                    updated_at = excluded.updated_at
                """,
                (workflow.name, payload, now, now),
            )

    def get_workflow(self, name: str) -> Optional[Workflow]:
        with self._tx() as cur:
            cur.execute("SELECT definition FROM workflows WHERE name = ?", (name,))
            row = cur.fetchone()
        if row is None:
            return None
        return Workflow.model_validate_json(row["definition"])

    def list_workflows(self) -> List[str]:
        with self._tx() as cur:
            cur.execute("SELECT name FROM workflows ORDER BY name")
            return [r["name"] for r in cur.fetchall()]

    def delete_workflow(self, name: str) -> bool:
        with self._tx() as cur:
            cur.execute("DELETE FROM workflows WHERE name = ?", (name,))
            return cur.rowcount > 0

    # --- runs --------------------------------------------------------------

    def save_run(self, result: RunResult, workflow_name: Optional[str]) -> str:
        run_id = uuid.uuid4().hex
        with self._tx() as cur:
            cur.execute(
                """
                INSERT INTO runs (id, workflow_name, status, final_node, result, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    workflow_name,
                    result.status,
                    result.final_node,
                    result.model_dump_json(),
                    _utcnow(),
                ),
            )
        return run_id

    def get_run(self, run_id: str) -> Optional[RunResult]:
        with self._tx() as cur:
            cur.execute("SELECT result FROM runs WHERE id = ?", (run_id,))
            row = cur.fetchone()
        if row is None:
            return None
        return RunResult.model_validate_json(row["result"])

    def list_runs(self, workflow_name: Optional[str] = None) -> List[dict]:
        with self._tx() as cur:
            if workflow_name is None:
                cur.execute(
                    "SELECT id, workflow_name, status, final_node, created_at "
                    "FROM runs ORDER BY created_at DESC"
                )
            else:
                cur.execute(
                    "SELECT id, workflow_name, status, final_node, created_at "
                    "FROM runs WHERE workflow_name = ? ORDER BY created_at DESC",
                    (workflow_name,),
                )
            return [dict(r) for r in cur.fetchall()]
