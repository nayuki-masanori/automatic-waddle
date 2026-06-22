"""FastAPI エンドポイントの統合テスト (SQLite 永続化 + Obsidian 連携)."""

import importlib

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path, monkeypatch):
    """テストごとに一時 DB と一時 vault を使うクライアントを作る."""
    monkeypatch.setenv("AW_DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("AW_VAULT_PATH", str(tmp_path / "vault"))
    import app.main as main

    importlib.reload(main)
    return TestClient(main.app)


WORKFLOW = {
    "name": "grading",
    "start": "decide",
    "nodes": [
        {
            "id": "decide",
            "type": "decision",
            "transitions": [
                {"to": "pass", "condition": "score >= 60"},
                {"to": "fail"},
            ],
        },
        {
            "id": "pass",
            "type": "task",
            "assign": {"grade": "'pass'"},
            "transitions": [{"to": "end"}],
        },
        {
            "id": "fail",
            "type": "task",
            "assign": {"grade": "'fail'"},
            "transitions": [{"to": "end"}],
        },
        {"id": "end", "type": "end"},
    ],
}


def test_health(client):
    assert client.get("/health").json()["status"] == "ok"


def test_register_and_run(client):
    resp = client.post("/workflows", json={"workflow": WORKFLOW})
    assert resp.status_code == 201

    assert "grading" in client.get("/workflows").json()

    run = client.post("/workflows/grading/run", json={"inputs": {"score": 75}})
    assert run.status_code == 200
    body = run.json()
    assert body["status"] == "completed"
    assert body["context"]["grade"] == "pass"


def test_persistence_across_reload(client, tmp_path, monkeypatch):
    """DB に保存され、アプリを作り直しても定義が残ることを確認する."""
    client.post("/workflows", json={"workflow": WORKFLOW})

    # 同じ DB / vault を指したまま app を再ロード
    import app.main as main

    importlib.reload(main)
    new_client = TestClient(main.app)
    assert "grading" in new_client.get("/workflows").json()


def test_run_history(client):
    client.post("/workflows", json={"workflow": WORKFLOW})
    client.post("/workflows/grading/run", json={"inputs": {"score": 75}})
    runs = client.get("/runs").json()
    assert len(runs) == 1
    run_id = runs[0]["id"]
    detail = client.get(f"/runs/{run_id}").json()
    assert detail["context"]["grade"] == "pass"


def test_run_missing_workflow(client):
    resp = client.post("/workflows/nope/run", json={"inputs": {}})
    assert resp.status_code == 404


def test_inline_run(client):
    resp = client.post("/run", json={"workflow": WORKFLOW, "inputs": {"score": 10}})
    assert resp.status_code == 200
    assert resp.json()["context"]["grade"] == "fail"


def test_invalid_workflow_rejected(client):
    bad = {"name": "bad", "start": "missing", "nodes": []}
    resp = client.post("/workflows", json={"workflow": bad})
    assert resp.status_code == 422


def test_obsidian_export_and_import_roundtrip(client):
    client.post("/workflows", json={"workflow": WORKFLOW})

    # ワークフロー定義を vault に書き出す
    exp = client.post("/obsidian/export/workflow/grading")
    assert exp.status_code == 200
    assert exp.json()["exported"].endswith(".md")

    # 一旦 DB から削除してから、vault からインポートして復元できることを確認
    assert client.delete("/workflows/grading").status_code == 204
    imp = client.post("/obsidian/import")
    assert imp.status_code == 200
    assert "grading" in imp.json()["imported"]
    assert "grading" in client.get("/workflows").json()


def test_obsidian_export_run(client):
    client.post("/workflows", json={"workflow": WORKFLOW})
    client.post("/workflows/grading/run", json={"inputs": {"score": 90}})
    run_id = client.get("/runs").json()[0]["id"]
    exp = client.post(f"/obsidian/export/run/{run_id}")
    assert exp.status_code == 200
    assert exp.json()["exported"].endswith(".md")
