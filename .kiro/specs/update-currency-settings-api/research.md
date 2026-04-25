# Research & Design Decisions

## Summary
- **Feature**: `update-currency-settings-api`
- **Discovery Scope**: Extension（既存システムへの機能追加）
- **Key Findings**:
  - `UserService.update_user` は既に `base_currency` 更新ロジックを持つが、通貨設定専用のエンドポイントとして分離が必要
  - `CurrencyConstants` と `UserService.VALID_CURRENCIES` の間に不整合あり（設計で `CurrencyConstants` に統一）
  - 既存の `get_currency_settings` エンドポイントと同じ認証・認可パターンを適用可能

## Research Log

### 既存コードパターン分析
- **Context**: 通貨設定更新APIの実装に必要な既存パターンの特定
- **Sources Consulted**:
  - `app/api/v1/user.py` - 既存の通貨設定取得エンドポイント
  - `app/services/user_service.py` - ユーザー更新ロジック
  - `app/constants.py` - 通貨定数定義
- **Findings**:
  - `get_currency_settings` エンドポイントは `user_bp` Blueprint に存在
  - `UserService.update_user` は `base_currency` 更新をサポート済み
  - 認証は `@jwt_required_custom` デコレータを使用
  - レスポンスは `success_response()` ユーティリティを使用
- **Implications**: 新規エンドポイントは既存パターンに準拠し、`UserService` の既存メソッドを活用可能

### 通貨バリデーションの不整合
- **Context**: サポート対象通貨の定義が複数箇所に存在
- **Sources Consulted**:
  - `app/constants.py` - `CurrencyConstants.all()` = ["USD", "JPY"]
  - `app/services/user_service.py` - `VALID_CURRENCIES` = {"JPY", "USD", "EUR", "GBP"}
- **Findings**:
  - `CurrencyConstants` は USD, JPY のみ定義
  - `UserService.VALID_CURRENCIES` は EUR, GBP も含む
  - OpenAPI仕様と要件は USD, JPY のみをサポート
- **Implications**: 本APIでは `CurrencyConstants` を使用し、一貫性を確保

## Architecture Pattern Evaluation

| Option | Description | Strengths | Risks / Limitations | Notes |
|--------|-------------|-----------|---------------------|-------|
| 既存update_user再利用 | PATCH /users/{userId} で通貨更新 | コード重複なし | エンドポイントが異なる、責任分離が不明確 | 不採用 |
| 新規エンドポイント追加 | PATCH /users/{userId}/settings/currency | OpenAPI仕様準拠、責任分離明確 | 新規コード追加 | 採用 |

## Design Decisions

### Decision: 通貨設定専用エンドポイントの新規作成
- **Context**: OpenAPI仕様に基づき、通貨設定専用のPATCH エンドポイントが必要
- **Alternatives Considered**:
  1. 既存 `update_user` エンドポイントの拡張 — 統合エンドポイント
  2. 通貨設定専用エンドポイントの新規作成 — 関心の分離
- **Selected Approach**: 通貨設定専用エンドポイントの新規作成
- **Rationale**: OpenAPI仕様に準拠し、通貨設定という特定のドメインに対する明確なAPIを提供
- **Trade-offs**: コード追加が必要だが、責任分離とAPI明確性のメリットが上回る
- **Follow-up**: テストでエンドポイントの分離が正しく機能することを確認

### Decision: CurrencyConstantsの使用
- **Context**: 通貨バリデーションの一元化
- **Alternatives Considered**:
  1. `UserService.VALID_CURRENCIES` を使用 — 現状維持
  2. `CurrencyConstants` を使用 — 一元化
- **Selected Approach**: `CurrencyConstants` を使用
- **Rationale**: プロジェクト全体での一貫性と、既存のGET通貨設定APIとの整合性
- **Trade-offs**: EUR, GBP が現時点ではサポート外となる
- **Follow-up**: 必要に応じて `CurrencyConstants` を拡張

## Risks & Mitigations
- 通貨コードの不整合 — `CurrencyConstants` に統一し、`UserService` も修正対象として検討
- 認可チェックの漏れ — 既存の `get_currency_settings` と同じパターンを適用

## References
- [OpenAPI Specification - settings.paths.yaml](../docs/openapi/paths/settings.paths.yaml)
- [CurrencyConstants - constants.py](../app/constants.py)
