# API 仕様ガイド

## 📋 レスポンス形式

成功レスポンス
```json
{
  "data": { ... },
  "meta": { ... }
}
```

エラーレスポンス
```json
{
  "error": {
    "code": 401,
    "name": "Unauthorized",
    "message": "Invalid credentials"
  }
}
```

## 🔐 認証

| メソッド | エンドポイント | 説明 |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | ユーザー新規登録 |
| POST | `/api/v1/auth/login` | ログイン |
| POST | `/api/v1/auth/refresh` | トークンリフレッシュ |

## 📦 サブスクリプション管理

| メソッド | エンドポイント | 説明 |
|--------|----------|-------------|
| GET | `/api/v1/subscriptions` | 一覧取得 |
| POST | `/api/v1/subscriptions` | 新規登録 |
| GET | `/api/v1/subscriptions/{id}` | 詳細取得 |
| PUT | `/api/v1/subscriptions/{id}` | 更新 |
| DELETE | `/api/v1/subscriptions/{id}` | 削除 |

## 💸 支払い履歴

| メソッド | エンドポイント | 説明 |
|--------|----------|-------------|
| GET | `/api/v1/payments` | 支払い履歴一覧 |
| POST | `/api/v1/payments` | 支払い記録作成 |

## 📚 OpenAPI ドキュメントの生成

ReDoc を使用して API 仕様書をレンダリングできます。

```bash
# バンドル
docker build -f docker/Dockerfile.oas-bundler -t redocly .
docker run --rm -v $(pwd):/app redocly bundle /app/docs/openapi/openapi.yaml -o /app/docs/openapi/build/openapi.yaml --ext yaml
```
