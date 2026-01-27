# 調査および設計上の決定事項

---
**目的**: 技術設計に情報を提供するための発見事項、アーキテクチャの調査、およびその根拠を記録する。

**使用法**:
- 発見フェーズ中の調査活動とその結果を記録する。
- `design.md` に記載するには詳細すぎる設計上の決定事項やトレードオフを文書化する。
- 将来の監査や再利用のために、参照資料と証拠を提供する。
---

## サマリー
- **機能**: `delete-payment-history-api`
- **発見の範囲**: シンプルな機能追加 (Simple Addition)
- **主な発見事項**:
  - `PaymentHistoryRepository` には既に `delete` メソッドが実装されている。
  - `PaymentHistoryService` に、所有権の検証を行う新しい `delete_payment` メソッドが必要である。
  - `app/api/v1/payment_history.py` に、新しい `DELETE /payments/{id}` エンドポイントが必要である。
  - `SubscriptionService` や `LabelService` にある既存のパターンを直接再利用できる。

## 調査ログ

### 既存実装の分析
- **コンテキスト**: `PaymentHistory` 関連のコンポーネントが削除機能を既にサポートしているか確認する。
- **参照ソース**: 
    - `app/repositories/payment_history_repository.py`
    - `app/services/payment_history_service.py`
    - `app/api/v1/payment_history.py`
- **発見事項**:
    - リポジトリ: `delete(self, payment_history: PaymentHistory)` が存在する。
    - サービス: `delete_payment` が不足している。既存の `update_payment` には適応可能な所有権ロジックがある。
    - API: `DELETE` ルートが不足している。
- **影響**: 
    - 実装は単純で、既存のリポジトリメソッドをサービスを通じてAPIに接続する形になる。

## 設計上の決定事項

### 決定: 既存リポジトリメソッドの再利用
- **コンテキスト**: 支払履歴レコードを物理削除する必要がある。
- **検討した代替案**:
  1. 論理削除の実装 (`deleted_at` カラムの追加)
  2. 物理削除 (レコードの削除)
- **選択したアプローチ**: 物理削除
- **根拠**: 要件において物理削除が指定されている。リポジトリは既に `session.delete()` を通じてこれをサポートしている。
- **トレードオフ**: データは永久に失われるが、要件に準拠し、データ管理が簡素化される。

### 決定: サービス層での検証
- **コンテキスト**: ユーザーが自分自身の支払履歴のみを削除できるようにする必要がある。
- **選択したアプローチ**: IDでレコードを取得し、`user_id` をチェックする。不一致の場合は `Forbidden` (または存在を隠すために `NotFound`) を発生させる。
- **根拠**: `SubscriptionService` および `LabelService` のセキュリティパターンと一貫している。

## リスクと緩和策
- **リスク 1**: データの誤削除。
  - **緩和策**: APIはID指定による明示的な `DELETE` である。フロントエンドで確認ダイアログを実装すべきである（バックエンドの範囲外だが、バックエンドは安全なプリミティブを提供する）。
- **リスク 2**: ログのオーバーヘッド。
  - **緩和策**: 要件に従い、重要な情報（payment_id, user_id）のみをログに記録し、個人情報（PII）は含めない。

## 参考文献
- [SQLAlchemy Cascades](https://docs.sqlalchemy.org/en/20/orm/cascades.html)
- [Flask-JWT-Extended Documentation](https://flask-jwt-extended.readthedocs.io/en/stable/)