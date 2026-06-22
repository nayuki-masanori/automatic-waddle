"""FastAPI エンドポイントの統合テスト."""

import pytest
from fastapi.testclient import TestClient

from app.main import app, _store


@pytest.fixture(autouse=True)
def _clear_store():
    _store.clear()
    yield
    _store.clear()


client = TestClient(app)


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


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_register_and_run():
    resp = client.post("/workflows", json={"workflow": WORKFLOW})
    assert resp.status_code == 201

    assert "grading" in client.get("/workflows").json()

    run = client.post("/workflows/grading/run", json={"inputs": {"score": 75}})
    assert run.status_code == 200
    body = run.json()
    assert body["status"] == "completed"
    assert body["context"]["grade"] == "pass"


def test_run_missing_workflow():
    resp = client.post("/workflows/nope/run", json={"inputs": {}})
    assert resp.status_code == 404


def test_inline_run():
    resp = client.post("/run", json={"workflow": WORKFLOW, "inputs": {"score": 10}})
    assert resp.status_code == 200
    assert resp.json()["context"]["grade"] == "fail"


def test_invalid_workflow_rejected():
    bad = {"name": "bad", "start": "missing", "nodes": []}
    resp = client.post("/workflows", json={"workflow": bad})
    assert resp.status_code == 422
