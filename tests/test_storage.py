"""SQLite ストレージの単体テスト."""

from app.models import RunResult, TraceStep, NodeType, Workflow
from app.storage import Storage


def _wf() -> Workflow:
    return Workflow.model_validate(
        {
            "name": "wf1",
            "start": "a",
            "nodes": [
                {"id": "a", "type": "task", "assign": {"x": "1"}, "transitions": [{"to": "end"}]},
                {"id": "end", "type": "end"},
            ],
        }
    )


def test_save_get_list_delete(tmp_path):
    store = Storage(str(tmp_path / "t.db"))
    store.save_workflow(_wf())
    assert store.list_workflows() == ["wf1"]
    loaded = store.get_workflow("wf1")
    assert loaded is not None and loaded.start == "a"
    assert store.delete_workflow("wf1") is True
    assert store.get_workflow("wf1") is None
    assert store.delete_workflow("wf1") is False


def test_upsert_overwrites(tmp_path):
    store = Storage(str(tmp_path / "t.db"))
    store.save_workflow(_wf())
    store.save_workflow(_wf())  # 同名で再保存しても重複しない
    assert store.list_workflows() == ["wf1"]


def test_persistence_reopen(tmp_path):
    db = str(tmp_path / "t.db")
    store = Storage(db)
    store.save_workflow(_wf())
    store.close()

    reopened = Storage(db)
    assert "wf1" in reopened.list_workflows()


def test_save_and_get_run(tmp_path):
    store = Storage(str(tmp_path / "t.db"))
    result = RunResult(
        status="completed",
        final_node="end",
        context={"x": 1},
        trace=[TraceStep(node_id="a", node_type=NodeType.TASK, assigned={"x": 1})],
    )
    run_id = store.save_run(result, workflow_name="wf1")
    loaded = store.get_run(run_id)
    assert loaded is not None and loaded.context == {"x": 1}
    runs = store.list_runs("wf1")
    assert len(runs) == 1 and runs[0]["id"] == run_id
