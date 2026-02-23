# 開発ワークフロー

## 🏗 開発フロー (TDD)

1. `/docs/test-list/` にテストリストを作成
2. テストコードの実装
3. 最小限のコードで実装
4. リファクタリング

## 🛠 コード品質管理

- **Ruff**: リンター・フォーマッター
- **Black**: コードフォーマッター (Ruffに統合済みの場合あり)
- **型ヒント**: 全関数に必須
- **Docstring**: Google形式

## 🌿 ブランチ戦略

```
main
├── develop/with-cline  (開発メイン)
├── feat/feature-name   (機能追加)
└── fix/bug-name        (バグ修正)
```

## 🏗 クリーンアーキテクチャ風の構成

- **app/api/v1/**: Webインターフェース層 (Flask Route)
- **app/services/**: ユースケース層 (Business Logic)
- **app/repositories/**: データアクセス層 (SQLAlchemy)
- **app/models/**: エンティティ層 (Database Schema)
