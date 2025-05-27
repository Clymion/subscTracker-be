# Test List: Authentication API

## Feature Description
認証APIのテストリスト。ログイン、登録、トークンリフレッシュ、ユーザー情報管理に関するテストケースを網羅。

## Related Requirements
- REQ-001: ユーザーはメールアドレスとパスワードでログインできること
- REQ-002: 新規ユーザー登録が可能であること
- REQ-003: JWTトークンによる認証が機能すること
- REQ-004: トークンのリフレッシュが可能であること
- REQ-005: ユーザー情報の取得・更新・削除が認証されたユーザーに対して行えること
- REQ-006: パスワード変更機能が正常に動作すること

## Test Categories

### Unit Tests

#### AuthService
- [ ] authenticate() が正しい資格情報でユーザーを返す
- [ ] authenticate() が誤った資格情報で None を返す
- [ ] register_user() が有効なデータでユーザーを作成する
- [ ] register_user() が重複メールで例外を投げる
- [ ] register_user() がパスワード不一致で例外を投げる

### Integration Tests

#### API Endpoints
- [ ] POST /api/v1/auth/login が有効な資格情報で 200 を返す
- [ ] POST /api/v1/auth/login が無効な資格情報で 401 を返す
- [ ] POST /api/v1/auth/register が有効なデータで 201 を返す
- [ ] POST /api/v1/auth/register が重複メールで 409 を返す
- [ ] POST /api/v1/auth/refresh が有効なリフレッシュトークンで 200 を返す
- [ ] GET /api/v1/users/{userId} が認証済みユーザーで 200 を返す
- [ ] GET /api/v1/users/{userId} が未認証で 401 を返す
- [ ] PATCH /api/v1/users/{userId} が認証済みユーザーで 200 を返す
- [ ] DELETE /api/v1/users/{userId} が認証済みユーザーで 204 を返す
- [ ] POST /api/v1/users/{userId}/change-password が認証済みユーザーで 200 を返す

### Error Handling Tests

- [ ] トークン期限切れで 401 エラーを返す
- [ ] 不正なトークンで 401 エラーを返す
- [ ] 権限不足で 403 エラーを返す
- [ ] バリデーションエラーで 400 エラーを返す

## Implementation Approach
1. AuthServiceの単体テストを作成
2. 認証APIエンドポイントの統合テストを作成
3. バリデーションとエラーハンドリングのテストを追加
4. テストを実行し、カバレッジを確認

## Dependencies
- Userモデル
- JWT設定
- データベース接続

## Estimated Effort
Medium (5-8 story points)

## Acceptance Criteria
- すべてのテストがパスすること
- 90%以上のテストカバレッジを達成すること
- APIパラメータ設計がOpenAPI仕様に準拠していること
