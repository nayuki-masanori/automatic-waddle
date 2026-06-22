"""Obsidian (Markdown vault) 連携.

双方向連携を提供する:

エクスポート (アプリ -> vault):
    実行結果 (trace) を、人が読みやすい Markdown ノートとして vault に書き出す。
    どのノードをどの条件で通過したかをテーブルで記録し、実行ログとして残す。

インポート (vault -> アプリ):
    vault 内の Markdown を読み、埋め込まれた JSON コードブロックを
    ワークフロー定義として取り込む。Obsidian で編集した定義を実行できる。

ノートはどちらも先頭に YAML フロントマターを持ち、``aw-type`` で種別
(``workflow`` / ``run``) を区別する。
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from app.models import RunResult, Workflow

# フロントマター (--- ... ---) を取り出す正規表現
_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
# ```json ... ``` コードブロックを取り出す正規表現
_JSON_BLOCK_RE = re.compile(r"```json\s*\n(.*?)\n```", re.DOTALL)


class ObsidianError(Exception):
    """Obsidian 連携に関するエラー."""


def _slugify(value: str) -> str:
    """ファイル名に使える安全な文字列へ変換する."""
    slug = re.sub(r"[^\w\-]+", "-", value, flags=re.UNICODE).strip("-")
    return slug or "untitled"


def _parse_frontmatter(text: str) -> dict:
    """フロントマターを簡易パースして dict で返す (キー: 値 の1行形式のみ)."""
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return {}
    meta: dict = {}
    for line in match.group(1).splitlines():
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        meta[key.strip()] = val.strip()
    return meta


class ObsidianVault:
    """Obsidian vault (ディレクトリ) への読み書きを担うクラス."""

    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.workflows_dir = self.vault_path / "Workflows"
        self.runs_dir = self.vault_path / "Runs"

    def _ensure_dirs(self) -> None:
        self.workflows_dir.mkdir(parents=True, exist_ok=True)
        self.runs_dir.mkdir(parents=True, exist_ok=True)

    # --- エクスポート ------------------------------------------------------

    def export_run(self, result: RunResult, run_id: str) -> Path:
        """実行結果 (trace) を Markdown ノートとして書き出し、パスを返す."""
        self._ensure_dirs()
        ts = datetime.now(timezone.utc)
        wf_name = result.final_node or "run"
        filename = f"{ts.strftime('%Y%m%d-%H%M%S')}-{_slugify(run_id[:8])}.md"
        path = self.runs_dir / filename
        path.write_text(self._render_run(result, run_id, ts), encoding="utf-8")
        return path

    def _render_run(self, result: RunResult, run_id: str, ts: datetime) -> str:
        lines: List[str] = []
        lines.append("---")
        lines.append("aw-type: run")
        lines.append(f"run-id: {run_id}")
        lines.append(f"status: {result.status}")
        lines.append(f"final-node: {result.final_node}")
        lines.append(f"created-at: {ts.isoformat()}")
        lines.append("---")
        lines.append("")
        lines.append(f"# 実行結果 `{run_id[:8]}`")
        lines.append("")
        lines.append(f"- **status**: {result.status}")
        lines.append(f"- **final node**: `{result.final_node}`")
        lines.append("")
        lines.append("## 実行経路 (trace)")
        lines.append("")
        lines.append("| # | node | type | condition | -> next | assigned |")
        lines.append("|---|------|------|-----------|---------|----------|")
        for i, step in enumerate(result.trace, start=1):
            cond = f"`{step.condition}`" if step.condition else ""
            nxt = f"`{step.chosen_transition}`" if step.chosen_transition else ""
            assigned = (
                ", ".join(f"{k}={v!r}" for k, v in step.assigned.items())
                if step.assigned
                else ""
            )
            lines.append(
                f"| {i} | `{step.node_id}` | {step.node_type.value} | {cond} | {nxt} | {assigned} |"
            )
        lines.append("")
        lines.append("## 最終 context")
        lines.append("")
        lines.append("```json")
        lines.append(json.dumps(result.context, ensure_ascii=False, indent=2))
        lines.append("```")
        lines.append("")
        return "\n".join(lines)

    def export_workflow(self, workflow: Workflow) -> Path:
        """ワークフロー定義を Markdown ノートとして書き出し、パスを返す.

        インポートで読み戻せるよう、定義 JSON をコードブロックに埋め込む。
        """
        self._ensure_dirs()
        path = self.workflows_dir / f"{_slugify(workflow.name)}.md"
        lines: List[str] = []
        lines.append("---")
        lines.append("aw-type: workflow")
        lines.append(f"name: {workflow.name}")
        lines.append(f"start: {workflow.start}")
        lines.append("---")
        lines.append("")
        lines.append(f"# {workflow.name}")
        lines.append("")
        if workflow.description:
            lines.append(workflow.description)
            lines.append("")
        lines.append("## 定義")
        lines.append("")
        lines.append("```json")
        lines.append(workflow.model_dump_json(indent=2))
        lines.append("```")
        lines.append("")
        path.write_text("\n".join(lines), encoding="utf-8")
        return path

    # --- インポート --------------------------------------------------------

    def import_workflow_file(self, path: Path) -> Workflow:
        """1 つの Markdown ファイルからワークフロー定義を取り込む."""
        text = path.read_text(encoding="utf-8")
        match = _JSON_BLOCK_RE.search(text)
        if not match:
            raise ObsidianError(f"no json code block found in {path.name}")
        try:
            data = json.loads(match.group(1))
        except json.JSONDecodeError as exc:
            raise ObsidianError(f"invalid json in {path.name}: {exc}") from exc
        try:
            return Workflow.model_validate(data)
        except Exception as exc:  # pydantic ValidationError 等
            raise ObsidianError(f"invalid workflow in {path.name}: {exc}") from exc

    def import_workflows(self) -> List[Workflow]:
        """vault の Workflows/ 配下を走査してワークフロー定義を取り込む.

        ``aw-type: workflow`` のフロントマターを持つノートのみ対象とする。
        """
        if not self.workflows_dir.exists():
            raise ObsidianError(f"workflows directory not found: {self.workflows_dir}")
        workflows: List[Workflow] = []
        for md in sorted(self.workflows_dir.glob("*.md")):
            text = md.read_text(encoding="utf-8")
            meta = _parse_frontmatter(text)
            if meta.get("aw-type") != "workflow":
                continue
            workflows.append(self.import_workflow_file(md))
        return workflows
