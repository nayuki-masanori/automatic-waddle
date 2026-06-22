"""FastAPI アプリケーション — 動的フロー実行エンジン.

ワークフロー定義と実行結果は SQLite に永続化される (再起動後も残る)。
Obsidian vault が設定されていれば、実行結果のエクスポートや vault からの
ワークフロー定義インポートも行える。

エンドポイント:
    POST   /workflows               ワークフローを登録 (永続化)
    GET    /workflows               登録済みワークフロー一覧
    GET    /workflows/{name}        ワークフロー定義を取得
    DELETE /workflows/{name}        ワークフローを削除
    POST   /workflows/{name}/run    入力を与えてワークフローを実行 (結果を永続化)
    POST   /run                     定義と入力を同時に渡してその場で実行
    GET    /runs                    実行履歴一覧
    GET    /runs/{run_id}           実行結果を取得
    POST   /obsidian/export/run/{run_id}      実行結果を vault に書き出す
    POST   /obsidian/export/workflow/{name}   ワークフロー定義を vault に書き出す
    POST   /obsidian/import                   vault からワークフロー定義を取り込む
"""

from __future__ import annotations

from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query

from app.config import get_db_path, get_vault_path
from app.engine.runner import WorkflowExecutionError, run_workflow
from app.models import (
    RunRequest,
    RunResult,
    Workflow,
    WorkflowCreate,
)
from app.obsidian import ObsidianError, ObsidianVault
from app.storage import Storage

app = FastAPI(
    title="automatic-waddle",
    description="条件分岐や入力に応じて実行経路が変わる動的フロー実行エンジン",
    version="0.2.0",
)

storage = Storage(get_db_path())


def _vault() -> ObsidianVault:
    """設定済みの Obsidian vault を返す。未設定なら 400 を返す。"""
    path = get_vault_path()
    if not path:
        raise HTTPException(
            status_code=400,
            detail="Obsidian vault is not configured (set AW_VAULT_PATH)",
        )
    return ObsidianVault(path)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "vault": get_vault_path()}


# --- workflows -------------------------------------------------------------


@app.post("/workflows", status_code=201)
def create_workflow(payload: WorkflowCreate) -> dict:
    wf = payload.workflow
    storage.save_workflow(wf)
    return {"name": wf.name, "nodes": len(wf.nodes)}


@app.get("/workflows")
def list_workflows() -> List[str]:
    return storage.list_workflows()


@app.get("/workflows/{name}", response_model=Workflow)
def get_workflow(name: str) -> Workflow:
    wf = storage.get_workflow(name)
    if wf is None:
        raise HTTPException(status_code=404, detail=f"workflow {name!r} not found")
    return wf


@app.delete("/workflows/{name}", status_code=204)
def delete_workflow(name: str) -> None:
    if not storage.delete_workflow(name):
        raise HTTPException(status_code=404, detail=f"workflow {name!r} not found")


# --- run -------------------------------------------------------------------


@app.post("/workflows/{name}/run", response_model=RunResult)
def run_registered_workflow(name: str, req: RunRequest) -> RunResult:
    wf = storage.get_workflow(name)
    if wf is None:
        raise HTTPException(status_code=404, detail=f"workflow {name!r} not found")
    try:
        result = run_workflow(wf, req.inputs, max_steps=req.max_steps)
    except WorkflowExecutionError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    storage.save_run(result, workflow_name=name)
    return result


class InlineRunRequest(RunRequest):
    """定義そのものを渡して即時実行するためのリクエスト."""

    workflow: Workflow


@app.post("/run", response_model=RunResult)
def run_inline(req: InlineRunRequest) -> RunResult:
    try:
        result = run_workflow(req.workflow, req.inputs, max_steps=req.max_steps)
    except WorkflowExecutionError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    storage.save_run(result, workflow_name=req.workflow.name)
    return result


# --- runs (履歴) -----------------------------------------------------------


@app.get("/runs")
def list_runs(workflow: Optional[str] = Query(default=None)) -> List[dict]:
    return storage.list_runs(workflow_name=workflow)


@app.get("/runs/{run_id}", response_model=RunResult)
def get_run(run_id: str) -> RunResult:
    result = storage.get_run(run_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"run {run_id!r} not found")
    return result


# --- Obsidian 連携 ---------------------------------------------------------


@app.post("/obsidian/export/run/{run_id}")
def export_run(run_id: str) -> dict:
    result = storage.get_run(run_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"run {run_id!r} not found")
    path = _vault().export_run(result, run_id)
    return {"exported": str(path)}


@app.post("/obsidian/export/workflow/{name}")
def export_workflow(name: str) -> dict:
    wf = storage.get_workflow(name)
    if wf is None:
        raise HTTPException(status_code=404, detail=f"workflow {name!r} not found")
    path = _vault().export_workflow(wf)
    return {"exported": str(path)}


@app.post("/obsidian/import")
def import_workflows() -> dict:
    """vault の Workflows/ からワークフロー定義を取り込み、DB に保存する."""
    try:
        workflows = _vault().import_workflows()
    except ObsidianError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    for wf in workflows:
        storage.save_workflow(wf)
    return {"imported": [wf.name for wf in workflows], "count": len(workflows)}
