"""Obsidian 連携の単体テスト."""

import pytest

from app.models import NodeType, RunResult, TraceStep, Workflow
from app.obsidian import ObsidianError, ObsidianVault


def _wf() -> Workflow:
    return Workflow.model_validate(
        {
            "name": "grading",
            "description": "点数で分岐",
            "start": "decide",
            "nodes": [
                {
                    "id": "decide",
                    "type": "decision",
                    "transitions": [
                        {"to": "pass", "condition": "score >= 60"},
                        {"to": "end"},
                    ],
                },
                {"id": "pass", "type": "task", "assign": {"grade": "'A'"}, "transitions": [{"to": "end"}]},
                {"id": "end", "type": "end"},
            ],
        }
    )


def test_export_then_import_roundtrip(tmp_path):
    vault = ObsidianVault(str(tmp_path / "vault"))
    path = vault.export_workflow(_wf())
    assert path.exists()
    assert "```json" in path.read_text(encoding="utf-8")

    imported = vault.import_workflows()
    assert len(imported) == 1
    assert imported[0].name == "grading"
    assert imported[0].start == "decide"


def test_export_run_creates_markdown(tmp_path):
    vault = ObsidianVault(str(tmp_path / "vault"))
    result = RunResult(
        status="completed",
        final_node="end",
        context={"score": 90, "grade": "A"},
        trace=[
            TraceStep(
                node_id="decide",
                node_type=NodeType.DECISION,
                chosen_transition="pass",
                condition="score >= 60",
            ),
            TraceStep(node_id="pass", node_type=NodeType.TASK, assigned={"grade": "A"}),
        ],
    )
    path = vault.export_run(result, run_id="abcd1234")
    text = path.read_text(encoding="utf-8")
    assert "aw-type: run" in text
    assert "score >= 60" in text
    assert "trace" in text


def test_import_missing_dir_raises(tmp_path):
    vault = ObsidianVault(str(tmp_path / "nonexistent"))
    with pytest.raises(ObsidianError):
        vault.import_workflows()


def test_import_ignores_non_workflow_notes(tmp_path):
    vault = ObsidianVault(str(tmp_path / "vault"))
    vault.export_workflow(_wf())
    # 関係ないノートを置いても無視される
    other = vault.workflows_dir / "note.md"
    other.write_text("---\naw-type: other\n---\n\n# memo\n", encoding="utf-8")
    imported = vault.import_workflows()
    assert [w.name for w in imported] == ["grading"]


def test_import_invalid_json_raises(tmp_path):
    vault = ObsidianVault(str(tmp_path / "vault"))
    vault._ensure_dirs()
    bad = vault.workflows_dir / "bad.md"
    bad.write_text(
        "---\naw-type: workflow\n---\n\n```json\n{not valid}\n```\n", encoding="utf-8"
    )
    with pytest.raises(ObsidianError):
        vault.import_workflows()
