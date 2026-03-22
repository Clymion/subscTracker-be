# Research & Design Decisions

---
**Purpose**: Capture discovery findings, architectural investigations, and rationale that inform the technical design.
---

## Summary
- **Feature**: `user-profile-api`
- **Discovery Scope**: Simple Addition
- **Key Findings**:
  - 機能はPhase 0で既に実装済み
  - 既存のレイヤードアーキテクチャ（API→Service→Repository）に準拠
  - テストコードの追加のみが必要

## Research Log

### 既存実装の確認
- **Context**: ギャップ分析の一環として、要件に対する実装状況を調査
- **Sources Consulted**:
  - `app/api/v1/user.py`
  - `app/services/user_service.py`
  - `app/repositories/user_repository.py`
  - `app/models/user.py`
- **Findings**:
  - GET/PATCH `/users/{userId}` エンドポイント実装済み
  - 認証・認可（JWT）の実装済み
  - 部分更新（PATCH）の実装済み
  - バリデーション（通貨コード、メール重複）の実装済み
- **Implications**: 設計フェーズは既存実装のドキュメント化が主目的

### テストコードの確認
- **Context**: テストカバレッジの確認
- **Sources Consulted**: `tests/` ディレクトリ
- **Findings**:
  - `tests/unit/test_user_model.py` は存在
  - `tests/integration/test_user_api.py` は存在しない
- **Implications**: 統合テストの追加が必要

## Architecture Pattern Evaluation

| Option | Description | Strengths | Risks / Limitations | Notes |
|--------|-------------|-----------|---------------------|-------|
| 既存レイヤードアーキテクチャ | API→Service→Repositoryの3層構造 | 既存パターンに準拠 | なし | 採用 |

## Design Decisions

### Decision: 既存実装の活用
- **Context**: 機能が既に実装済みであるため、設計は文書化が主目的
- **Alternatives Considered**:
  1. 再実装 — 不要
  2. 既存実装の文書化 — 採用
- **Selected Approach**: 既存実装をそのまま採用し、設計ドキュメントを作成
- **Rationale**: 既存実装は要件を完全に満たしており、追加の開発コストが不要
- **Trade-offs**: なし
- **Follow-up**: テストコードの追加

## Risks & Mitigations
- テストカバレッジ不足 — 統合テストの追加で対応

## References
- [Flask Blueprints](https://flask.palletsprojects.com/en/latest/blueprints/) — APIルーティング
- [Flask-JWT-Extended](https://flask-jwt-extended.readthedocs.io/) — 認証
