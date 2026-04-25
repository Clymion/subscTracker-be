# Research & Design Decisions

---
**Purpose**: Capture discovery findings, architectural investigations, and rationale that inform the technical design.

**Usage**:
- Log research activities and outcomes during the discovery phase.
- Document design decision trade-offs that are too detailed for `design.md`.
- Provide references and evidence for future audits or reuse.
---

## Summary
- **Feature**: `update-user-api`
- **Discovery Scope**: Extension (既存システムへの機能拡張)
- **Key Findings**:
  - 既存の3層アーキテクチャ（API → Service → Repository）を踏襲
  - 既存のPATCH実装は基本的に存在するが、バリデーションが不完全
  - 空のJSONオブジェクト`{}`のハンドリングが要件と異なる（現状は成功、要件は400エラー）

## Research Log

### 既存コードベース分析
- **Context**: ユーザー更新APIの既存実装を把握し、拡張ポイントを特定
- **Sources Consulted**: 
  - `app/api/v1/user.py`
  - `app/services/user_service.py`
  - `app/repositories/user_repository.py`
  - `app/models/user.py`
  - `app/common/auth_middleware.py`
  - `app/constants.py`
  - `app/exceptions.py`
- **Findings**:
  - PATCH /users/{userId} エンドポイントは既に実装済み
  - `UserService.update_user()` は基本機能を持つが、以下のバリデーションが不足:
    - ユーザー名の長さチェック（3-32文字）
    - 空のJSONオブジェクト`{}`の拒否
  - メール重複チェックは既存実装に含まれる
  - 通貨コード検証は既存実装に含まれるが、GBP/EURも許可されている（OpenAPI仕様と一致）
- **Implications**: 既存コードの修正として実装、新規作成ではなく拡張

### 認証・認可パターン
- **Context**: 既存の認証・認可パターンを確認
- **Sources Consulted**: 
  - `app/common/auth_middleware.py`
  - `tests/integration/test_user_api.py`
- **Findings**:
  - `@jwt_required_custom` デコレータでJWT認証を強制
  - `get_jwt_identity()` でユーザーIDを取得
  - 401/403エラーは標準形式で返却
- **Implications**: 既存パターンをそのまま使用

### レスポンス形式
- **Context**: 既存のレスポンス形式を確認
- **Sources Consulted**:
  - `app/common/response_utils.py`
  - `app/api/v1/user.py`
- **Findings**:
  - 成功時: `success_response()` で `{"data": {...}}` 形式
  - エラー時: `{"error": {"code": ..., "message": ...}}` 形式
- **Implications**: 既存パターンを踏襲

## Architecture Pattern Evaluation

| Option | Description | Strengths | Risks / Limitations | Notes |
|--------|-------------|-----------|---------------------|-------|
| 既存3層拡張 | API → Service → Repositoryの既存パターンを拡張 | 一貫性、既存テストとの互換性 | なし | 採用 |
| 新規サービス層 | 別のサービスクラスを作成 | 分離 | 過剰設計 | 却下 |

## Design Decisions

### Decision: 既存実装の拡張アプローチ
- **Context**: ユーザー更新APIの既存実装を改善
- **Alternatives Considered**:
  1. 既存コードを拡張 — 既存の`update_user`メソッドにバリデーションを追加
  2. 新規作成 — 別のメソッド/クラスを作成
- **Selected Approach**: 既存コードの拡張
- **Rationale**: 既存のテストやアーキテクチャとの一貫性を維持
- **Trade-offs**: 既存コードへの影響を最小限に抑える vs コードの重複を避ける
- **Follow-up**: 既存テストが通ることを確認

### Decision: バリデーションロジックの配置
- **Context**: 入力バリデーションをどこに実装するか
- **Alternatives Considered**:
  1. サービス層 — `UserService.update_user()`内で実装
  2. API層 — エンドポイントで実装
  3. 専用バリデータ — 別クラスに分離
- **Selected Approach**: サービス層で実装（既存パターン踏襲）
- **Rationale**: ビジネスロジックとしてのバリデーションはサービス層に配置する既存パターンと整合
- **Trade-offs**: サービス層の責務増加 vs 一貫したバリデーション
- **Follow-up**: なし

### Decision: 空のJSONオブジェクトのハンドリング
- **Context**: 空のJSONオブジェクト`{}`を受信した場合の処理
- **Alternatives Considered**:
  1. 400エラー返却 — 不正なリクエストとして拒否
  2. 成功返却 — 変更なしとして成功
- **Selected Approach**: 400エラー返却
- **Rationale**: クライアントのエラーを明示的に通知し、APIの誤用を防止
- **Trade-offs**: クライアント側での対応が必要 vs 明確なエラー通知
- **Follow-up**: テストで検証

## Risks & Mitigations
- 既存テストとの互換性 — 既存テストを確認し、必要に応じて更新
- 空オブジェクト対応の既存テスト — 現状成功を返すテストを400エラーに更新

## References
- [Flask-JWT-Extended Documentation](https://flask-jwt-extended.readthedocs.io/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [OpenAPI Specification](./docs/openapi/openapi.yaml)
