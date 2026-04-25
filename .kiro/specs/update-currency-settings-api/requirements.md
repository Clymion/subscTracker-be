# Requirements Document

## Introduction

本ドキュメントは、ユーザーの通貨設定を更新するAPI `PATCH /users/{userId}/settings/currency` の要件を定義する。このAPIは、認証済みユーザーが自分の基準通貨設定を変更するために使用される。

## Requirements

### Requirement 1: 認証・認可
**Objective:** As a 認証済みユーザー, I want 自分の通貨設定のみ更新できる, so that 他のユーザーの設定が不正に変更されることを防ぐ

#### Acceptance Criteria
1. When リクエストに有効なJWTトークンが含まれる場合, the API shall リクエストを処理し通貨設定を更新する
2. When リクエストにJWTトークンが含まれない場合, the API shall 401 Unauthorizedエラーを返す
3. When リクエストのJWTトークンが期限切れの場合, the API shall 401 Unauthorizedエラーを返す
4. When リクエストされたuserIdがJWTのユーザーIDと一致しない場合, the API shall 403 Forbiddenエラーを返す

### Requirement 2: リクエストバリデーション
**Objective:** As a システム, I want リクエストボディを適切に検証できる, so that 不正なデータの更新を防ぐ

#### Acceptance Criteria
1. When リクエストボディがJSON形式でない場合, the API shall 400 Bad Requestエラーを返す
2. When リクエストボディにbase_currencyフィールドが含まれない場合, the API shall 400 Bad Requestエラーを返す
3. When base_currencyが空文字の場合, the API shall 400 Bad Requestエラーを返す
4. When base_currencyがISO 4217形式の3文字でない場合, the API shall 400 Bad Requestエラーを返す
5. When base_currencyがサポートされていない通貨コードの場合, the API shall 400 Bad Requestエラーを返す

### Requirement 3: 通貨設定の更新
**Objective:** As a 認証済みユーザー, I want 自分の基準通貨を変更できる, so that サブスクリプション管理における基準通貨を自分の環境に合わせて設定できる

#### Acceptance Criteria
1. When 有効なbase_currencyでリクエストされた場合, the API shall ユーザーのbase_currencyを更新する
2. When ユーザーが存在しない場合, the API shall 404 Not Foundエラーを返す
3. The API shall 更新成功時に更新後のbase_currencyを含むレスポンスを返す

### Requirement 4: レスポンス形式
**Objective:** As a クライアントアプリケーション, I want 一貫したJSONレスポンス形式を受け取る, so that 処理が容易になり統合が簡素化される

#### Acceptance Criteria
1. When 通貨設定の更新に成功した場合, the API shall 以下の形式のJSONレスポンスを返す:
   ```json
   {
     "data": {
       "base_currency": "string"
     }
   }
   ```
2. When エラーが発生した場合, the API shall 統一されたエラーレスポンス形式を返す:
   ```json
   {
     "error": {
       "code": "integer",
       "name": "string",
       "message": "string"
     }
   }
   ```

### Requirement 5: セキュリティ要件
**Objective:** As a システム管理者, I want APIが適切なセキュリティ対策を講じる, so that ユーザーデータが保護される

#### Acceptance Criteria
1. The API shall JWT認証をすべてのリクエストに要求する
2. The API shall ユーザーが自分以外のユーザーの設定を更新することを防止する
3. When 認可エラーが発生した場合, the API shall セキュリティイベントをログに記録する

### Requirement 6: サポート対象通貨
**Objective:** As a システム, I want サポートする通貨を明確に定義する, so that ユーザーが有効な通貨のみ設定できる

#### Acceptance Criteria
1. The API shall JPY（日本円）をサポートする
2. The API shall USD（米ドル）をサポートする
