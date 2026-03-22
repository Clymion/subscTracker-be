# Requirements Document

## Introduction

ユーザープロフィールAPIは、認証済みユーザーが自身のプロフィール情報（ユーザー名、メールアドレス、基準通貨）を取得・更新するためのREST APIを提供する。このAPIは、サブスクリプション管理アプリケーションの設定画面におけるプロフィール設定機能を支える。

## Requirements

### Requirement 1: プロフィール取得

**Objective:** ユーザーとして、自分のプロフィール情報を確認したい。これにより、現在の設定内容を把握できる。

#### Acceptance Criteria
1. When ユーザーがプロフィール取得リクエストを送信する, the User Profile API shall ユーザーID、ユーザー名、メールアドレス、基準通貨、作成日時を含むプロフィール情報を返す
2. When 未認証ユーザーがプロフィール取得リクエストを送信する, the User Profile API shall 401 Unauthorizedエラーを返す
3. When ユーザーが他のユーザーのプロフィールを取得しようとする, the User Profile API shall 403 Forbiddenエラーを返す
4. If 指定されたユーザーIDが存在しない, the User Profile API shall 404 Not Foundエラーを返す

### Requirement 2: プロフィール更新

**Objective:** ユーザーとして、自分のプロフィール情報を更新したい。これにより、表示名や連絡先、基準通貨を変更できる。

#### Acceptance Criteria
1. When ユーザーが有効なプロフィール更新リクエストを送信する, the User Profile API shall 更新後のプロフィール情報を返す
2. When ユーザー名を更新する, the User Profile API shall 3文字以上32文字以下のユーザー名を受け入れる
3. When メールアドレスを更新する, the User Profile API shall 有効なメールフォーマットのアドレスを受け入れる
4. When 基準通貨を更新する, the User Profile API shall JPY、USD、EUR、GBPのいずれかの通貨コードを受け入れる
5. If 更新後のメールアドレスが既に使用されている, the User Profile API shall 400 Bad Requestエラーを返す
6. If 無効な通貨コードが指定される, the User Profile API shall 400 Bad Requestエラーを返す
7. When 未認証ユーザーがプロフィール更新リクエストを送信する, the User Profile API shall 401 Unauthorizedエラーを返す
8. When ユーザーが他のユーザーのプロフィールを更新しようとする, the User Profile API shall 403 Forbiddenエラーを返す
9. When 空のリクエストボディが送信される, the User Profile API shall 400 Bad Requestエラーを返す

### Requirement 3: 部分更新サポート

**Objective:** ユーザーとして、変更が必要なフィールドのみを更新したい。これにより、不要な入力を省ける。

#### Acceptance Criteria
1. When リクエストに一部のフィールドのみが含まれる, the User Profile API shall 指定されたフィールドのみを更新し、他のフィールドは変更しない
2. When いずれのフィールドも含まれない空のオブジェクトが送信される, the User Profile API shall 現在のプロフィール情報を変更せずに返す

### Requirement 4: レスポンス形式

**Objective:** 開発者として、一貫したAPIレスポンス形式を持たい。これにより、クライアント実装が容易になる。

#### Acceptance Criteria
1. When プロフィール取得・更新が成功する, the User Profile API shall `data`フィールドにプロフィール情報を含むJSONオブジェクトを返す
2. When エラーが発生する, the User Profile API shall `error`フィールドにコードとメッセージを含むJSONオブジェクトを返す
3. The User Profile API shall すべてのレスポンスにおいて`Content-Type: application/json`ヘッダーを返す
