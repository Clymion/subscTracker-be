# Research & Design Decisions

---
**Purpose**: Capture discovery findings, architectural investigations, and rationale that inform the technical design.

**Usage**:
- Log research activities and outcomes during the discovery phase.
- Document design decision trade-offs that are too detailed for `design.md`.
- Provide references and evidence for future audits or reuse.
---

## Summary
- **Feature**: `delete-user-api`
- **Discovery Scope**: Extension (既存ユーザーAPIへのDELETE機能追加)
- **Key Findings**:
  - 既存の3層アーキテクチャ(API/Service/Repository)に従い、既存パターンを踏襲
  - Userモデルは既にcascade="all, delete-orphan"で関連データのカスケード削除設定済み
  - パスワード検証にはUser.check_password()メソッドを使用

## Research Log

### 既存コードパターンの分析
- **Context**: 削除API実装にあたり、既存のDELETE実装パターンを調査
- **Sources Consulted**:
  - `app/api/v1/subscription.py:173-188` - DELETE実装パターン
  - `app/api/v1/label.py:153` - DELETE実装パターン
  - `app/services/subscription_service.py:218` - Service層の削除ロジック
  - `app/repositories/subscription_repository.py:113` - Repository層の削除ロジック
- **Findings**:
  - API層: `@jwt_required_custom`デコレータで認証、204 No Content返却
  - Service層: ユーザー権限チェック、ビジネスロジック実行
  - Repository層: `session.delete()` + `session.commit()`パターン
  - エラーハンドリング: カスタム例外クラス(NotFoundError等)を使用
- **Implications**: UserDeleteAPIでも同様パターンを踏襲

### Userモデルのカスケード削除確認
- **Context**: ユーザー削除時の関連データ削除動作を確認
- **Sources Consulted**: `app/models/user.py:42-48`
- **Findings**:
  - `subscriptions`: `cascade="all, delete-orphan"` 設定済み
  - `labels`: `cascade="all, delete-orphan"` 設定済み
  - `payment_histories`: `cascade="all, delete-orphan"` 設定済み
- **Implications**: User削除時に自動的に関連データも削除されるため、個別削除処理は不要

### OpenAPI仕様との整合性確認
- **Context**: API仕様書との整合性を確認
- **Sources Consulted**: `docs/openapi/paths/auth.paths.yaml:172-209`
- **Findings**:
  - DELETE `/users/{userId}` エンドポイント定義済み
  - RequestBody: `password` フィールド必須
  - Response: 204 No Content
  - エラー: 400, 401, 403, 404
- **Implications**: パスワード確認機能が必須要件

## Architecture Pattern Evaluation

| Option | Description | Strengths | Risks / Limitations | Notes |
|--------|-------------|-----------|---------------------|-------|
| 3層パターン踏襲 | API→Service→Repository | 既存コードとの一貫性 | なし | 採用 |
| 物理削除 | データベースから完全削除 | データ完全削除、GDPR準拠 | 復旧不可 | 採用(OpenAPI仕様準拠) |
| 論理削除 | deleted_atフラグ追加 | 復旧可能 | データ蓄積、プライバシー懸念 | 却下 |

## Design Decisions

### Decision: パスワード確認による削除実行
- **Context**: 誤操作・不正削除防止のため、削除前にパスワード確認が必要
- **Alternatives Considered**:
  1. パスワード確認なし - 誤操作リスク高
  2. パスワード確認あり - OpenAPI仕様準拠
- **Selected Approach**: リクエストボディでパスワードを受け取り、User.check_password()で検証
- **Rationale**: OpenAPI仕様およびセキュリティ要件に準拠
- **Trade-offs**: ユーザー利便性 vs セキュリティのバランス
- **Follow-up**: パスワード検証失敗時のエラーメッセージを適切に設定

### Decision: JWTトークンの無効化
- **Context**: ユーザー削除後もトークンが有効だと、削除済みユーザーがアクセス可能
- **Alternatives Considered**:
  1. トークン無効化なし - セキュリティリスク
  2. トークンブロックリスト - インフラ複雑化
  3. 短いトークン有効期限 - 運用負荷
- **Selected Approach**: 現段階では明示的な無効化は実装せず、トークン有効期限に依存
- **Rationale**: 現行システムにトークンブロックリストがなく、スコープ外
- **Trade-offs**: トークン有効期限内は削除済みユーザーがアクセス可能(許容範囲)
- **Follow-up**: 将来的なトークン無効化機構の検討

## Risks & Mitigations
- パスワード検証失敗のブルートフォース攻撃 → レート制限の検討(将来)
- 削除後のデータ復旧不可 → ユーザーへの確認UI推奨(フロントエンド側)
- トークン有効期限内の不正アクセス → トークン有効期限を短めに設定(既定3600秒)

## References
- [OpenAPI仕様書](../docs/openapi/paths/auth.paths.yaml) - API定義
- [Userモデル](../app/models/user.py) - カスケード設定
- [Subscription削除パターン](../app/api/v1/subscription.py:173) - 参照実装
