"""FastAPI アプリケーション — 動的フロー実行エンジン.

エンドポイント:
    POST   /workflows          ワークフローを登録
    GET    /workflows          登録済みワークフロー一覧
    GET    /workflows/{name}   ワークフロー定義を取得
    DELETE /workflows/{name}   ワークフローを削除
    POST   /workflows/{name}/run   入力を与えてワークフローを実行
    POST   /run                定義と入力を同時に渡してその場で実行
"""

from __future__ import annotations

from typing import Dict, List

from fastapi import FastAPI, HTTPException

from app.engine.runner import WorkflowExecutionError, run_workflow
from app.models import (
    RunRequest,
    RunResult,
    Workflow,
    WorkflowCreate,
)

app = FastAPI(
    title="automatic-waddle",
    description="条件分岐や入力に応じて実行経路が変わる動的フロー実行エンジン",
    version="0.1.0",
)

# 簡易のインメモリストア (本番では永続化層に差し替える)
_store: Dict[str, Workflow] = {}


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/workflows", status_code=201)
def create_workflow(payload: WorkflowCreate) -> dict:
    wf = payload.workflow
    _store[wf.name] = wf
    return {"name": wf.name, "nodes": len(wf.nodes)}


@app.get("/workflows")
def list_workflows() -> List[str]:
    return list(_store.keys())


@app.get("/workflows/{name}", response_model=Workflow)
def get_workflow(name: str) -> Workflow:
    wf = _store.get(name)
    if wf is None:
        raise HTTPException(status_code=404, detail=f"workflow {name!r} not found")
    return wf


@app.delete("/workflows/{name}", status_code=204)
def delete_workflow(name: str) -> None:
    if name not in _store:
        raise HTTPException(status_code=404, detail=f"workflow {name!r} not found")
    del _store[name]


@app.post("/workflows/{name}/run", response_model=RunResult)
def run_registered_workflow(name: str, req: RunRequest) -> RunResult:
    wf = _store.get(name)
    if wf is None:
        raise HTTPException(status_code=404, detail=f"workflow {name!r} not found")
    try:
        return run_workflow(wf, req.inputs, max_steps=req.max_steps)
    except WorkflowExecutionError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


class InlineRunRequest(RunRequest):
    """定義そのものを渡して即時実行するためのリクエスト."""

    workflow: Workflow


@app.post("/run", response_model=RunResult)
def run_inline(req: InlineRunRequest) -> RunResult:
    try:
        return run_workflow(req.workflow, req.inputs, max_steps=req.max_steps)
    except WorkflowExecutionError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
