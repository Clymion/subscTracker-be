# Research & Design Decisions Template

---
**Purpose**: Capture discovery findings, architectural investigations, and rationale that inform the technical design.

**Usage**:
- Log research activities and outcomes during the discovery phase.
- Document design decision trade-offs that are too detailed for `design.md`.
- Provide references and evidence for future audits or reuse.
---

## Summary
- **Feature**: `get-currency-settings-api`
- **Discovery Scope**: Simple Addition
- **Key Findings**:
  - `base_currency`フィールドはUserモデルに既に存在し、デフォルト値"USD"で定義済み
  - 既存の`user_bp` Blueprintと認証パターンをそのまま再利用可能
  - 新規依存関係は不要。既存の`UserService.get_user_by_id()`を再利用

## Research Log

### 既存コードパターン調査
- **Context**: 統合ポイントと再利用可能なコンポーネントの特定
- **Sources Consulted**:
  - `app/api/v1/user.py` - 既存ユーザーAPIパターン
  - `app/services/user_service.py` - ユーザーサービス実装
  - `app/repositories/user_repository.py` - リポジトリパターン
  - `app/common/auth_middleware.py` - JWT認証デコレータ
  - `app/common/response_utils.py` - レスポンスユーティリティ
- **Findings**:
  - `user_bp` Blueprintが`/api/v1`プレフィックスで登録済み
  - 認証: `@jwt_required_custom`デコレータ + `get_jwt_identity()`でユーザーID取得
  - 認可: `int(current_user_id) != user_id`パターンで所有権確認
  - レスポンス: `success_response({"data": {...}})`形式
  - ユーザー存在確認: `UserService.get_user_by_id()`を使用
- **Implications**:
  - 新規コンポーネント不要。`user_bp`へのエンドポイント追加のみ
  - 既存の`UserService`と`UserRepository`を再利用

### データモデル確認
- **Context**: base_currencyフィールドの仕様確認
- **Sources Consulted**:
  - `app/models/user.py` - Userモデル定義
  - `migrations/versions/36e602ae28aa_add_base_currency_to_user.py` - マイグレーション
- **Findings**:
  - `base_currency: Mapped[str]` - String(3), nullable=False, server_default="USD"
  - ISO 4217形式の3文字通貨コード
  - `UserService.VALID_CURRENCIES = {"JPY", "USD", "EUR", "GBP"}`
- **Implications**:
  - データベース変更不要
  - OpenAPIスキーマ`CurrencySettings`は`base_currency`のみを返す

## Architecture Pattern Evaluation

| Option | Description | Strengths | Risks / Limitations | Notes |
|--------|-------------|-----------|---------------------|-------|
| user_bp拡張 | 既存user.pyにエンドポイント追加 | 最小変更、既存パターン継承 | ファイルサイズ増加 | 既存パターンとの整合性が最優先 |
| 新規settings_bp | 新Blueprint作成 | 関心の分離 | Blueprint登録、テスト追加必要 | オーバーエンジニアリング |

**Selected Approach**: `user_bp`拡張

## Design Decisions

### Decision: エンドポイント配置
- **Context**: 新しい通貨設定取得APIの配置場所
- **Alternatives Considered**:
  1. `user_bp`に新規エンドポイント追加
  2. 新規`settings_bp`作成
- **Selected Approach**: `user_bp`に`/users/<int:user_id>/settings/currency`エンドポイントを追加
- **Rationale**: 既存のユーザー関連エンドポイントと整合。最小変更で実装可能。
- **Trade-offs**: user.pyファイルが大きくなるが、新規Blueprint作成のオーバーヘッドを回避
- **Follow-up**: 今後settings系エンドポイントが増える場合はsettings_bp分離を検討

### Decision: サービス層の再利用
- **Context**: ビジネスロジックの実装場所
- **Alternatives Considered**:
  1. 新規`SettingsService`作成
  2. 既存`UserService.get_user_by_id()`を再利用
- **Selected Approach**: 既存`UserService.get_user_by_id()`を再利用
- **Rationale**: 通貨設定はUserモデルの一部であり、新規サービス層は不要
- **Trade-offs**: なし（シンプルな取得操作）
- **Follow-up**: なし

## Risks & Mitigations
- 既存機能への影響なし — 新規エンドポイント追加のみ
- パフォーマンス影響なし — 既存のクエリと同等

## References
- [OpenAPI Specification - CurrencySettings](docs/openapi/components/schemas/settings.schemas.yaml)
- [Flask Blueprint Documentation](https://flask.palletsprojects.com/en/latest/blueprints/)
