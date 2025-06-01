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
- [x] authenticate() が正しい資格情報でユーザーを返す
- [x] authenticate() が誤った資格情報で None を返す
- [x] authenticate() が存在しないメールアドレスで None を返す
- [x] authenticate() が空のデータベースで None を返す
- [x] authenticate() がケースセンシティブなメールで適切に処理
- [x] register_user() が有効なデータでユーザーを作成する
- [x] register_user() が重複メールで例外を投げる
- [x] register_user() が重複ユーザー名で例外を投げる
- [x] register_user() がパスワード不一致で例外を投げる
- [x] register_user() が必須フィールド不足で例外を投げる
- [x] register_user() が無効な値で例外を投げる
- [x] register_user() がパスワードを適切にハッシュ化する

#### User Model
- [x] ユーザー作成で全フィールドが正しく設定される
- [x] パスワード設定でハッシュが作成される
- [x] 正しいパスワードで認証が成功する
- [x] 間違ったパスワードで認証が失敗する
- [x] 異なるパスワードで異なるハッシュが生成される
- [x] 同じパスワードでもソルトにより異なるハッシュが生成される
- [x] 文字列表現が正しいフォーマットで返される
- [x] 特殊文字やUnicode文字のパスワードが正しく処理される

### Integration Tests

#### API Endpoints - Login
- [x] POST /api/v1/auth/login が有効な資格情報で 200 を返す
- [x] POST /api/v1/auth/login が無効なメールで 401 を返す
- [x] POST /api/v1/auth/login が間違ったパスワードで 401 を返す
- [x] POST /api/v1/auth/login がメール不足で 400+ を返す
- [x] POST /api/v1/auth/login がパスワード不足で 400+ を返す
- [x] POST /api/v1/auth/login が空のJSONで 400+ を返す

#### API Endpoints - Register
- [x] POST /api/v1/auth/register が有効なデータで 201 を返す
- [x] POST /api/v1/auth/register が重複メールで 400 を返す
- [x] POST /api/v1/auth/register がパスワード不一致で 400 を返す
- [x] POST /api/v1/auth/register が必須フィールド不足で 400+ を返す

#### API Endpoints - Refresh Token
- [x] POST /api/v1/auth/refresh が有効なリフレッシュトークンで 200 を返す
- [x] POST /api/v1/auth/refresh がトークン不足で 401 を返す
- [x] POST /api/v1/auth/refresh がアクセストークンで 401 を返す
- [x] POST /api/v1/auth/refresh が無効なトークンで 401 を返す
- [x] POST /api/v1/auth/refresh が期限切れトークンで TOKEN_EXPIRED を返す

#### Complete Authentication Flows
- [x] 完全な登録→ログイン→トークンリフレッシュフロー
- [x] 無効な資格情報での認証フロー
- [x] 複数ユーザーの独立した認証

### Error Handling Tests

- [x] トークン期限切れで 401 エラーと適切なメッセージを返す
- [x] 不正なトークンで 401 エラーを返す
- [x] 権限不足で 403 エラーを返す
- [x] バリデーションエラーで 400 エラーを返す
- [x] 無効なメール形式で認証失敗を返す
- [x] 無効なパスワード形式で登録失敗を返す

### Token Validation Tests
- [x] 期限切れトークンで適切なエラーを返す
- [x] 不正なトークン形式で適切なエラーを返す
- [x] トークン不足で適切なエラーを返す
- [x] 無効なBearer形式で適切なエラーを返す

## Implementation Approach
1. ✅ AuthServiceの単体テストを作成
2. ✅ 認証APIエンドポイントの統合テストを作成
3. ✅ バリデーションとエラーハンドリングのテストを追加
4. ✅ テストを実行し、カバレッジを確認

## Dependencies
- ✅ Userモデル
- ✅ JWT設定
- ✅ データベース接続

## Estimated Effort
Medium (5-8 story points)

## Acceptance Criteria
- ✅ すべてのテストがパスすること
- ✅ 90%以上のテストカバレッジを達成すること
- ✅ APIパラメータ設計がOpenAPI仕様に準拠していること

## Implementation Status
**COMPLETED** - 認証API、AuthService、Userモデルのすべてのテストが実装され、完全なテストカバレッジを提供している。
