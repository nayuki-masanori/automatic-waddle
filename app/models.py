"""ワークフロー定義と実行結果の Pydantic モデル."""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, model_validator


class NodeType(str, Enum):
    """ノードの種類."""

    START = "start"
    TASK = "task"
    DECISION = "decision"
    END = "end"


class Transition(BaseModel):
    """ノードから次ノードへの遷移.

    ``condition`` が真と評価された最初の遷移が選ばれる。``condition`` が
    ``None`` の遷移は「デフォルト（どの条件にも当てはまらない場合）」として扱う。
    """

    to: str = Field(..., description="遷移先ノードの id")
    condition: Optional[str] = Field(
        default=None,
        description="遷移条件式。None ならデフォルト遷移として最後に評価される。",
    )


class Node(BaseModel):
    """ワークフローを構成するノード."""

    id: str = Field(..., description="ノードを一意に識別する id")
    type: NodeType = Field(default=NodeType.TASK)
    # TASK ノードで実行する代入式。context のキーに式の評価結果を代入する。
    assign: Dict[str, str] = Field(
        default_factory=dict,
        description="{ 変数名: 式 } 形式。task ノードで context を更新する。",
    )
    transitions: List[Transition] = Field(default_factory=list)

    @model_validator(mode="after")
    def _check_terminal(self) -> "Node":
        if self.type == NodeType.END and self.transitions:
            raise ValueError(f"end node {self.id!r} must not have transitions")
        return self


class Workflow(BaseModel):
    """ノードの集合からなるワークフロー定義."""

    name: str
    description: str = ""
    start: str = Field(..., description="開始ノードの id")
    nodes: List[Node]

    @model_validator(mode="after")
    def _validate_graph(self) -> "Workflow":
        ids = [n.id for n in self.nodes]
        if len(ids) != len(set(ids)):
            raise ValueError("node ids must be unique")
        id_set = set(ids)
        if self.start not in id_set:
            raise ValueError(f"start node {self.start!r} not found in nodes")
        for node in self.nodes:
            for tr in node.transitions:
                if tr.to not in id_set:
                    raise ValueError(
                        f"node {node.id!r} has transition to unknown node {tr.to!r}"
                    )
        return self

    def node_map(self) -> Dict[str, Node]:
        return {n.id: n for n in self.nodes}


class WorkflowCreate(BaseModel):
    """ワークフロー登録リクエスト."""

    workflow: Workflow


class RunRequest(BaseModel):
    """ワークフロー実行リクエスト."""

    inputs: Dict[str, Any] = Field(default_factory=dict)
    max_steps: int = Field(default=100, ge=1, le=10_000)


class TraceStep(BaseModel):
    """実行トレースの 1 ステップ."""

    node_id: str
    node_type: NodeType
    assigned: Dict[str, Any] = Field(default_factory=dict)
    chosen_transition: Optional[str] = None
    condition: Optional[str] = None


class RunResult(BaseModel):
    """ワークフロー実行結果."""

    status: str
    final_node: Optional[str]
    context: Dict[str, Any]
    trace: List[TraceStep]
