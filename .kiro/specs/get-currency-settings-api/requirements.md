# Requirements Document

## Introduction

本ドキュメントは、ユーザーの通貨設定を取得するAPI `GET /users/{userId}/settings/currency` の要件を定義する。このAPIは、認証済みユーザーが自分の基準通貨設定を取得するために使用される。

## Requirements

### Requirement 1: 認証・認可
**Objective:** As a 認証済みユーザー, I want 自分の通貨設定にのみアクセスできる, so that 他のユーザーの設定が不正に閲覧されることを防ぐ

#### Acceptance Criteria
1. When リクエストに有効なJWTトークンが含まれる場合, the API shall リクエストを処理し通貨設定を返す
2. When リクエストにJWTトークンが含まれない場合, the API shall 401 Unauthorizedエラーを返す
3. When リクエストのJWTトークンが期限切れの場合, the API shall 401 Unauthorizedエラーを返す
4. When リクエストされたuserIdがJWTのユーザーIDと一致しない場合, the API shall 403 Forbiddenエラーを返す

### Requirement 2: 通貨設定の取得
**Objective:** As a 認証済みユーザー, I want 自分の通貨設定を取得できる, so that サブスクリプション管理における基準通貨や為替レート設定を確認できる

#### Acceptance Criteria
1. When 有効なuserIdでリクエストされた場合, the API shall ユーザーの通貨設定を返す
2. When ユーザーが存在しない場合, the API shall 404 Not Foundエラーを返す
3. The API shall base_currency（基準通貨）を含むレスポンスを返す
4. The API shall ISO 4217形式の3文字通貨コードとしてbase_currencyを返す

### Requirement 3: レスポンス形式
**Objective:** As a クライアントアプリケーション, I want 一貫したJSONレスポンス形式を受け取る, so that 処理が容易になり統合が簡素化される

#### Acceptance Criteria
1. When 通貨設定の取得に成功した場合, the API shall 以下の形式のJSONレスポンスを返す:
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

### Requirement 4: セキュリティ要件
**Objective:** As a システム管理者, I want APIが適切なセキュリティ対策を講じる, so that ユーザーデータが保護される

#### Acceptance Criteria
1. The API shall JWT認証をすべてのリクエストに要求する
2. The API shall ユーザーが自分以外のユーザーの設定にアクセスすることを防止する
3. When 認可エラーが発生した場合, the API shall セキュリティイベントをログに記録する
