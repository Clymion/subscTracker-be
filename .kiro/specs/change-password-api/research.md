# Research & Design Decisions

## Summary
- **Feature**: `change-password-api`
- **Discovery Scope**: Extension
- **Key Findings**:
  - 既存の`UserService`と`delete_user`メソッドのパターンを踏襲可能
  - パスワード検証には`user.check_password()`、設定には`user.set_password()`を使用
  - 新しい例外クラスは不要（`UserNotFoundError`、`InvalidPasswordError`を再利用）

## Research Log

### 既存パターンの分析
- **Context**: パスワード変更APIの実装にあたり、既存のユーザー管理コードのパターンを調査
- **Sources Consulted**:
  - `app/api/v1/user.py` - ユーザーAPIエンドポイント
  - `app/services/user_service.py` - ユーザーサービス
  - `app/models/user.py` - ユーザーモデル
  - `app/exceptions.py` - カスタム例外
- **Findings**:
  - `delete_user`メソッドで既にパスワード確認パターンが確立されている
  - `UserNotFoundError`、`InvalidPasswordError`が定義済み
  - `@jwt_required_custom`デコレータと`get_jwt_identity()`で認証・認可を実装
  - `success_response()`で一貫したレスポンス形式を提供
- **Implications**: 新規コンポーネントは最小限で、既存パターンの拡張のみで実装可能

### パスワードハッシュ化の確認
- **Context**: 要件3.5で指定されたwerkzeugのハッシュ化関数の使用確認
- **Sources Consulted**: `app/models/user.py`
- **Findings**:
  - `set_password`メソッドが`werkzeug.security.generate_password_hash`を使用
  - `check_password`メソッドが`werkzeug.security.check_password_hash`を使用
- **Implications**: Userモデルのメソッドをそのまま利用可能

### バリデーション定数の確認
- **Context**: パスワード長バリデーションの最小値確認
- **Sources Consulted**: `app/constants.py`
- **Findings**:
  - `ValidationConstants.PASSWORD_MIN_LENGTH = 8`
- **Implications**: 既存の定数を再利用可能

## Architecture Pattern Evaluation

| Option | Description | Strengths | Risks / Limitations | Notes |
|--------|-------------|-----------|---------------------|-------|
| API層への直接追加 | user.pyに新しいエンドポイントを追加 | 最小限の変更、一貫性 | なし | 採用 |
| 新しい認証サービス | 専用の認証サービスを作成 | 関心の分離 | 過剰設計、既存パターンとの不一致 | 却下 |

## Design Decisions

### Decision: UserServiceへのchange_passwordメソッド追加
- **Context**: パスワード変更ロジックの配置場所
- **Alternatives Considered**:
  1. AuthServiceに追加 — 認証関連のため
  2. UserServiceに追加 — ユーザー管理のため
- **Selected Approach**: UserServiceに`change_password`メソッドを追加
- **Rationale**: 既存の`delete_user`メソッドと同じパターン（パスワード確認＋ユーザー操作）
- **Trade-offs**: UserServiceが少し肥大化するが、一貫性を優先
- **Follow-up**: テストでパスワード検証の境界値を確認

### Decision: エンドポイントパスの決定
- **Context**: APIエンドポイントのURL設計
- **Alternatives Considered**:
  1. `POST /api/v1/users/{userId}/change-password` — RESTfulアクション
  2. `PATCH /api/v1/users/{userId}/password` — リソース指向
- **Selected Approach**: `POST /api/v1/users/{userId}/change-password`
- **Rationale**: 要件定義で指定されたパスに従う。また、パスワード変更は複雑な操作（現在のパスワード確認を含む）のため、アクション指向のPOSTが適切
- **Trade-offs**: 厳密なREST原則からは逸脱するが、実用性を優先
- **Follow-up**: OpenAPI仕様書の更新

## Risks & Mitigations
- セキュリティリスク: パスワードがログに出力される — **対策**: ログ出力時にパスワードフィールドを除外
- ブルートフォース攻撃 — **対策**: 現段階ではスコープ外（別途レート制限機能で対応予定）
- 既存機能への影響 — **対策**: 既存メソッドを変更せず、新規メソッドのみ追加

## References
- [Flask-JWT-Extended Documentation](https://flask-jwt-extended.readthedocs.io/) — JWT認証パターン
- [Werkzeug Security](https://werkzeug.palletsprojects.com/en/stable/utils/#module-werkzeug.security) — パスワードハッシュ化
