# Research & Design Decisions: Payment History Update API

---
**Purpose**: Capture discovery findings, architectural investigations, and rationale that inform the technical design.

**Usage**:
- Log research activities and outcomes during the discovery phase.
- Document design decision trade-offs that are too detailed for `design.md`.
- Provide references and evidence for future audits or reuse.
---

## Summary
- **Feature**: `update-payment-history-api`
- **Discovery Scope**: Extension (Existing System)
- **Key Findings**:
  - 既存の `PaymentHistoryService` と `PaymentHistoryRepository` を拡張することで実装可能。
  - 通貨または支払日が変更された場合、`ExchangeRateService` を再利用して為替レートの再計算が必要。
  - API層では `PATCH` メソッドを使用し、Marshmallow で部分更新のバリデーションを行う必要がある。

## Research Log

### Existing Code Analysis
- **Context**: 既存のコードベースにおける支払履歴の処理方法と統合ポイントの確認。
- **Sources Consulted**:
  - `app/services/payment_history_service.py`
  - `app/repositories/payment_history_repository.py`
  - `app/api/v1/payment_history.py`
  - `app/services/exchange_rate_service.py`
- **Findings**:
  - `PaymentHistoryRepository` は `save()` メソッドで更新も処理可能（SQLAlchemyのsession管理下にある場合）。
  - `PaymentHistoryService.create_payment` に為替レート取得と計算ロジックが存在するため、これを参照・再利用できる。
  - `ExchangeRateService.get_exchange_rate` は `(ExchangeRate, bool)` を返し、逆レートの判定も行っている。
- **Implications**:
  - `PaymentHistoryService` に `update_payment` メソッドを追加する。
  - バリデーションスキーマとして `PaymentUpdateRequestSchema` (または既存スキーマの `partial=True`) が必要。

### Update Logic & Exchange Rates
- **Context**: 更新時にどのような条件で為替レートを再計算すべきかの検討。
- **Findings**:
  - `currency` (通貨) または `payment_date` (支払日) が変更された場合、レートが変わるため再計算が必須。
  - `subscription_id` が変更された場合、`subscription_name` の更新が必要（履歴としての整合性を保つため）。
  - 金額 (`amount`) のみが変更された場合、既存のレートを使って `converted_amount` を再計算するだけで良い。
- **Implications**:
  - `update_payment` メソッド内で、変更フィールドに応じた条件分岐が必要。

## Architecture Pattern Evaluation

| Option | Description | Strengths | Risks / Limitations | Notes |
|--------|-------------|-----------|---------------------|-------|
| Service Layer Extension | 既存のServiceクラスにメソッド追加 | シンプル、既存ロジックと凝集度が高い | Serviceクラスが肥大化する可能性 | 今回はメソッド1つ追加程度なので許容範囲 |
| New Service Class | `PaymentUpdateService` を新規作成 | 責務分離が明確 | 依存関係の注入が増える、コードが分散する | 過剰設計の恐れあり |

**Selected Approach**: Service Layer Extension (既存Serviceへの追加)

## Design Decisions

### Decision: PATCH Method for Partial Updates
- **Context**: RESTful APIとしての更新メソッドの選択。
- **Alternatives Considered**:
  1. `PUT`: リソース全体の置換。クライアントが全データを送る必要がある。
  2. `PATCH`: リソースの部分更新。変更したいフィールドのみ送信する。
- **Selected Approach**: `PATCH`
- **Rationale**: ユーザーは金額だけ、日付だけを修正したいケースが多く、効率的であるため。OpenAPI仕様とも一致。
- **Trade-offs**: 実装が若干複雑になる（更新フィールドの判定など）。

### Decision: Validation Schema Strategy
- **Context**: 入力データのバリデーション方法。
- **Selected Approach**: 専用の `PaymentUpdateRequestSchema` を作成し、全フィールドを `optional` に設定する。
- **Rationale**: `Create` 用スキーマを `partial=True` で使い回すことも可能だが、更新時特有の制約（例: IDは変更不可など）を将来的に入れる可能性を考慮し、分離または明示的な定義を行う。現状は `PaymentCreateRequestSchema` と似た構造だが、すべてのフィールドが必須ではない。

## Risks & Mitigations
- **Risk**: 為替レートが存在しない日付への変更。
  - **Mitigation**: `ExchangeRateService` が `ResourceNotFoundError` を投げた場合、API層で `400 Bad Request` に変換してユーザーに通知する。
- **Risk**: 他人のデータの更新。
  - **Mitigation**: Service層で `user_id` による所有権チェックを厳密に行う。
