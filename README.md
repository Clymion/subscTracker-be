# サブスクリプション管理アプリ - Backend API

個人のサブスクリプションサービスを効率的に管理するためのWebアプリケーションのバックエンドAPIです。

## 📋 プロジェクト概要

このプロジェクトは、複数のサブスクリプションサービスを利用している個人ユーザーが、支出を正確に把握し、効率的に管理できるようにするためのRESTful APIを提供します。

### 主な目的
- サブスクリプションの登録、編集、削除機能
- 支払い履歴の管理と分析
- 為替レートの自動取得と通貨変換
- 支払い期限のリマインダー通知
- 支出の可視化と分析レポート

## 🚀 主要機能

### 実装済み機能 ✅
- **認証・認可システム**
  - JWT認証によるユーザー管理
  - アクセストークンとリフレッシュトークンの発行
  - セキュアなパスワードハッシュ化
  
- **共通基盤**
  - 標準化されたAPIレスポンス形式
  - ページネーション機能
  - 包括的なエラーハンドリング
  - 構造化ログ機能
  - 環境設定管理（pydantic-settings）

- **テスト基盤**
  - 包括的なユニットテスト（90%+カバレッジ）
  - 統合テスト（API エンドポイント）
  - テストデータファクトリ
  - CI/CD準備完了

- **サブスクリプション管理**
  - CRUD操作（作成・読取・更新・削除）
  - ラベルによる分類
  - ステータス管理（お試し中、一時停止など）

### 開発予定機能 🔄
- **支払い履歴管理**
  - 支払い記録の登録・編集
  - 多通貨対応
  - 為替レート自動取得
  
- **通知システム**
  - 支払い期限リマインダー
  - メール・プッシュ通知
  
- **分析機能**
  - 支出分析レポート
  - 月次・年次サマリー

## 🛠 技術スタック

### Backend Framework
- **Flask 3.1.0** - 軽量なWebフレームワーク
- **Python 3.13** - 最新の型ヒント機能を活用

### 認証・セキュリティ
- **flask-jwt-extended** - JWT認証
- **Werkzeug** - セキュアなパスワードハッシュ化

### データ管理
- **SQLAlchemy 2.x** - ORM
- **SQLite** - 軽量データベース（開発・本番共用）

### バリデーション・設定
- **Pydantic 2.x** - データバリデーション
- **pydantic-settings** - 環境設定管理

### 開発・テスト
- **pytest** - テストフレームワーク
- **Black + Ruff** - コード品質管理
- **Poetry** - 依存関係管理
- **Docker** - 開発環境の統一

## 📁 プロジェクト構造

```
subsc-be-sandbox1/
├── app/
│   ├── api/v1/           # APIエンドポイント
│   ├── common/           # 共通ユーティリティ
│   ├── models/           # データモデル
│   ├── services/         # ビジネスロジック
│   ├── config.py         # 設定管理
│   └── constants.py      # 定数定義
├── tests/
│   ├── unit/             # ユニットテスト
│   ├── integration/      # 統合テスト
│   └── fixtures/         # テストフィクスチャ
├── docs/
│   ├── openapi/          # API仕様書
│   ├── db/               # データベース設計
│   └── test-list/        # TDDテストリスト
├── memory-bank/          # プロジェクト管理情報
└── .clinerules/          # 開発ガイドライン
```

## 🚀 セットアップ

### 前提条件
- Docker & Docker Compose
- Python 3.13+ (ローカル開発の場合)

### 開発環境の起動

1. **リポジトリのクローン**
```bash
git clone https://github.com/Clymion/subscTracker-be1.git
cd subsc-be-sandbox1
```

2. **Docker Composeで起動**
```bash
docker-compose up --build
```

3. **API動作確認**
```bash
curl http://localhost:5000/api/v1/auth/register
```

### ローカル開発

1. **Poetryで依存関係をインストール**
```bash
poetry install
```

2. **環境変数の設定**
```bash
cp .env.example .env
# .envファイルを編集
```

3. **テストの実行**
```bash
poetry run pytest
```

4. **開発サーバーの起動**
```bash
poetry run flask --app app run --debug
```

## 📚 API仕様

### 認証エンドポイント

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | ユーザー新規登録 |
| POST | `/api/v1/auth/login` | ログイン |
| POST | `/api/v1/auth/refresh` | トークンリフレッシュ |

### レスポンス形式

**成功レスポンス**
```json
{
  "data": {
    "user": {
      "id": "1",
      "username": "testuser",
      "email": "test@example.com"
    }
  },
  "meta": {}
}
```

**エラーレスポンス**
```json
{
  "error": {
    "code": 401,
    "name": "Unauthorized",
    "message": "Invalid credentials"
  }
}
```

### API仕様書
詳細なAPI仕様は `/docs/openapi/` ディレクトリのYAMLファイルを参照してください。

## 🧪 テスト

### テスト実行
```bash
# 全テスト実行
poetry run pytest

# カバレッジレポート付き
poetry run pytest --cov=app --cov-report=html

# 特定のテストカテゴリ実行
poetry run pytest -m unit
poetry run pytest -m integration
poetry run pytest -m auth
```

### テスト構成
- **ユニットテスト**: 個別コンポーネントのテスト
- **統合テスト**: コンポーネント間の連携テスト
- **APIテスト**: HTTPエンドポイントのE2Eテスト

### テストカバレッジ
現在のテストカバレッジ: **90%+**

## 🏗 開発フロー

### TDD（テスト駆動開発）
1. `/docs/test-list/` にテストリストを作成
2. テストコードの実装
3. 最小限のコードで実装
4. リファクタリング

### コード品質
- **Ruff**: リンター・フォーマッター
- **Black**: コードフォーマッター
- **型ヒント**: 全関数に必須
- **Docstring**: Google形式

### ブランチ戦略
```
main
├── develop/with-cline
├── feat/feature-name
└── fix/bug-name
```

## 📈 開発状況

### 完了済み
- ✅ プロジェクト基盤設計
- ✅ 認証・認可システム
- ✅ 共通処理（エラー、ログ、設定管理）
- ✅ テスト基盤
- ✅ 開発環境整備
- ✅ サブスクリプション管理API
- ✅ 支払い履歴管理API

### 開発中

### 予定
- 📋 設定関連API
- 📋 通知サブシステム
- 📋 分析・レポート機能

## 🔧 設定

### 環境変数

| 変数名 | 説明 | デフォルト値 |
|--------|------|-------------|
| `DB_HOST` | データベースホスト | localhost |
| `DB_PORT` | データベースポート | 5432 |
| `DB_NAME` | データベース名 | 必須 |
| `JWT_SECRET_KEY` | JWT署名キー | 必須 |
| `API_PORT` | APIサーバーポート | 5000 |
| `DEBUG` | デバッグモード | false |

### 本番環境設定
- SQLiteファイルベース
- JWT認証
- 構造化ログ
- エラーモニタリング

## 📄 ドキュメント

- [MVP提案書](docs/MVP-proposal.md)
- [システム設計書](docs/system-proposal.md)
- [データベース設計](docs/db/table-definition.md)
- [開発ガイドライン](.clinerules/)
- [テストリスト](docs/test-list/)

## 🤝 コントリビューション

1. Issueを作成して機能追加や修正を提案
2. フィーチャーブランチを作成
3. TDDに従ってテストと実装を行う
4. プルリクエストを作成

### 開発ガイドライン
詳細な開発ルールは `.clinerules/` ディレクトリを参照してください。

## 📝 ライセンス

このプロジェクトは個人開発プロジェクトです。

## 🙋‍♂️ 作者

**Clymion** - [GitHub](https://github.com/Clymion)

---

## 📞 サポート

質問や問題がある場合は、GitHubのIssueを作成してください。
