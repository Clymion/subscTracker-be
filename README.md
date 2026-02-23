# サブスクリプション管理アプリ - Backend API

個人のサブスクリプションサービスを効率的に管理するためのバックエンドAPIです。

## 📋 プロジェクト概要

- 複数のサブスクリプションサービスの一括管理。
- 為替レート自動取得による多通貨対応。
- 支払い履歴の自動生成と分析。
- SQLite + Litestream による可用性の確保。

## 🚀 最小セットアップ (Docker)

```bash
docker-compose up --build
```
詳細は [セットアップ・実行ガイド](docs/setup.md) を参照。

## 📁 主要ドキュメント

- **[セットアップと実行](docs/setup.md)**: Prerequisites, Installation, Data Replication.
- **[API 仕様ガイド](docs/api-guide.md)**: Endpoints, Response formats, OpenAPI.
- **[開発ワークフロー](docs/development-workflow.md)**: TDD, Code quality, Branching.
- **[システム設計書](docs/system-proposal.md)**: Architecture, Tech stack.
- **[データベース設計](docs/db/table-definition.md)**: ER Diagram, Table schemas.

## 🛠 技術スタック

- **Backend**: Python 3.13, Flask 3.1.0, Poetry
- **Database**: SQLite3, SQLAlchemy 2.0
- **Availability**: Litestream (S3/GCS Replication)
- **Testing**: pytest (90%+ Coverage)

## 📈 開発状況

詳細は [MVP企画書](docs/MVP-proposal.md) および [機能リスト](docs/feature-list.md) を参照。

---

## 🙋‍♂️ 作者
**Clymion** - [GitHub](https://github.com/Clymion)
