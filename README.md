# automatic-waddle

条件分岐や入力に応じて実行経路が変わる**動的フロー実行エンジン**。
Python + FastAPI で実装。

ワークフローを JSON でノード（ステップ）の集合として定義し、各ノードの
遷移条件 (`condition`) を入力やそれまでの実行結果 (context) に基づいて
評価しながら、次に進むノードを動的に決定して実行します。

ワークフロー定義と実行結果は **SQLite に永続化**され、サーバーを再起動しても
残ります。さらに **Obsidian (Markdown vault) と双方向に連携**でき、実行結果を
ノートとして書き出したり、vault のノートからワークフロー定義を取り込めます。

## セットアップ

```bash
pip install -r requirements.txt
```

## 起動

```bash
uvicorn app.main:app --reload
```

起動後、API ドキュメント (Swagger UI) は http://127.0.0.1:8000/docs で確認できます。

### 設定 (環境変数)

| 環境変数 | 説明 | デフォルト |
|----------|------|-----------|
| `AW_DB_PATH` | SQLite データベースのパス | `automatic_waddle.db` |
| `AW_VAULT_PATH` | Obsidian vault のパス（未設定なら Obsidian 連携は無効） | （なし） |

```bash
AW_DB_PATH=./data/aw.db AW_VAULT_PATH=~/ObsidianVault uvicorn app.main:app --reload
```

## API

| メソッド | パス | 説明 |
|----------|------|------|
| GET    | `/health` | ヘルスチェック |
| POST   | `/workflows` | ワークフロー登録（永続化） |
| GET    | `/workflows` | 登録済み一覧 |
| GET    | `/workflows/{name}` | 定義取得 |
| DELETE | `/workflows/{name}` | 削除 |
| POST   | `/workflows/{name}/run` | 入力を与えて実行（結果を永続化） |
| POST   | `/run` | 定義と入力を渡して即時実行 |
| GET    | `/runs` | 実行履歴一覧（`?workflow=名前` で絞り込み） |
| GET    | `/runs/{run_id}` | 実行結果（trace 付き）を取得 |
| POST   | `/obsidian/export/run/{run_id}` | 実行結果を vault に Markdown で書き出す |
| POST   | `/obsidian/export/workflow/{name}` | ワークフロー定義を vault に書き出す |
| POST   | `/obsidian/import` | vault からワークフロー定義を取り込む |

## 永続化

ワークフロー定義は `workflows` テーブル、実行結果は `runs` テーブルに
JSON として保存されます（`app/storage.py`）。サーバー不要の SQLite を使うため、
追加のミドルウェアなしで再起動後もデータが残ります。

## Obsidian 連携

`AW_VAULT_PATH` を設定すると、指定した vault の下に次の構成でノートを読み書きします。

```
<vault>/
├── Workflows/   ワークフロー定義ノート (aw-type: workflow)
└── Runs/        実行結果ノート (aw-type: run)
```

- **エクスポート（アプリ → vault）**: 実行結果は trace（どのノードをどの条件で
  通過したか）のテーブルと最終 context を持つ Markdown ノートになります。
- **インポート（vault → アプリ）**: `Workflows/` 配下の、`aw-type: workflow` の
  フロントマターを持つノートに埋め込まれた JSON コードブロックを読み取り、
  ワークフロー定義として DB に取り込みます。Obsidian 上で編集した定義を
  そのまま実行できます（双方向）。

## ワークフロー定義

```jsonc
{
  "name": "grading",
  "start": "decide",
  "nodes": [
    {
      "id": "decide",
      "type": "decision",
      "transitions": [
        { "to": "high", "condition": "score >= 80" },
        { "to": "mid",  "condition": "score >= 60" },
        { "to": "low" }                                // condition 省略 = デフォルト遷移
      ]
    },
    { "id": "high", "type": "task", "assign": { "grade": "'A'" }, "transitions": [{ "to": "end" }] },
    { "id": "mid",  "type": "task", "assign": { "grade": "'B'" }, "transitions": [{ "to": "end" }] },
    { "id": "low",  "type": "task", "assign": { "grade": "'F'" }, "transitions": [{ "to": "end" }] },
    { "id": "end",  "type": "end" }
  ]
}
```

- **ノードの種類**: `start` / `task` / `decision` / `end`
- **`assign`**: `{ 変数名: 式 }`。式を評価して context を更新する（task ノード）
- **`transitions`**: 条件を上から順に評価し、最初に真になった遷移を選ぶ。
  `condition` を省略した遷移はデフォルト（どの条件にも当てはまらない場合）として採用される。

### 実行例

```bash
curl -X POST http://127.0.0.1:8000/run \
  -H 'Content-Type: application/json' \
  -d '{ "workflow": { ... }, "inputs": { "score": 95 } }'
```

レスポンスには最終 context に加え、どのノードをどの条件で通過したかの
`trace`（実行トレース）が含まれます。

## 条件式について

条件式・代入式は組み込み `eval` を使わず、AST をホワイトリストで制限した
安全な評価器 (`app/engine/evaluator.py`) で評価します。

- 算術 (`+ - * / // % **`)、比較 (`== != < <= > >=`, `in`, `not in`)、
  論理 (`and`, `or`, `not`)、三項演算 (`x if c else y`)
- リスト/辞書アクセス、属性アクセス（ダンダー属性は禁止）
- 一部の組み込み関数のみ許可 (`len`, `min`, `max`, `abs`, `round`,
  `str`, `int`, `float`, `bool`, `sum`, `sorted`, `any`, `all`)

## テスト

```bash
pytest
```
