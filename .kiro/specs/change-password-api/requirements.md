# 要件定義書

## 概要

本ドキュメントは、パスワード変更API `POST /api/v1/users/{userId}/change-password` の要件を定義する。このAPIは、認証済みユーザーが自分のパスワードを安全に変更するための機能を提供する。

## 要件

### 要件 1: パスワード変更の基本機能

**目的:** 認証済みユーザーとして、自分のパスワードを変更したい。なぜなら、セキュリティ向上やパスワード忘れ時の対応が必要だからだ。

#### 受け入れ基準

1. When ユーザーが `POST /api/v1/users/{userId}/change-password` にリクエストを送信する, the User API shall 現在のパスワードを検証し、新しいパスワードに更新する
2. When パスワード変更が成功する, the User API shall 200 OK ステータスと成功メッセージを返す
3. When ユーザーが存在しない, the User API shall 404 Not Found エラーを返す

### 要件 2: 現在のパスワード確認

**目的:** ユーザーとして、パスワード変更前に現在のパスワード確認を行いたい。なぜなら、不正なパスワード変更を防ぐためだ。

#### 受け入れ基準

1. When ユーザーがパスワード変更リクエストを送信する, the User API shall リクエストボディに`current_password`フィールドを要求する
2. When 現在のパスワードが正しくない, the User API shall 400 Bad Request エラーを返す
3. When 現在のパスワードが指定されていない, the User API shall 400 Bad Request エラーを返す

### 要件 3: 新しいパスワードの検証

**目的:** システム管理者として、強力なパスワードポリシーを適用したい。なぜなら、アカウントのセキュリティを確保するためだ。

#### 受け入れ基準

1. When ユーザーがパスワード変更リクエストを送信する, the User API shall リクエストボディに`new_password`フィールドを要求する
2. When 新しいパスワードが8文字未満のとき, the User API shall 400 Bad Request エラーを返す
3. When 新しいパスワードが指定されていない, the User API shall 400 Bad Request エラーを返す
4. When 新しいパスワードが空文字列のとき, the User API shall 400 Bad Request エラーを返す
5. The User API shall 新しいパスワードをwerkzeugの`generate_password_hash`でハッシュ化して保存する

### 要件 4: 認証・認可

**目的:** 認証済みユーザーとして、自分のパスワードのみ変更したい。なぜなら、他のユーザーのパスワードを不正に変更されるのを防ぐためだ。

#### 受け入れ基準

1. When リクエストに有効なJWTトークンが含まれない, the User API shall 401 Unauthorized エラーを返す
2. When JWTトークンのユーザーIDとパスパラメータのユーザーIDが一致しない, the User API shall 403 Forbidden エラーを返す
3. While ユーザーが認証済み, the User API shall 自分のパスワードのみ変更を許可する

### 要件 5: リクエスト形式

**目的:** APIクライアント開発者として、明確なリクエスト形式を知りたい。なぜなら、クライアントアプリケーションを正しく実装できるからだ。

#### 受け入れ基準

1. When ユーザーがパスワード変更リクエストを送信する, the User API shall JSON形式のリクエストボディを受け付ける
2. The User API shall `current_password`と`new_password`の2つのフィールドを要求する
3. When 無効なJSON形式のリクエストを受信したとき, the User API shall 400 Bad Request エラーを返す

### 要件 6: レスポンス形式

**目的:** APIクライアント開発者として、一貫したレスポンス形式を受け取りたい。なぜなら、クライアントアプリケーションを効率的に開発できるからだ。

#### 受け入れ基準

1. When パスワード変更が正常に完了したとき, the User API shall `data`フィールドに成功メッセージを含むJSONレスポンスを返す
2. When パスワード変更が正常に完了したとき, the User API shall HTTPステータスコード200を返す
3. When エラーが発生したとき, the User API shall `error`フィールドにエラーコードとメッセージを含むJSONレスポンスを返す
4. The User API shall 既存の共通レスポンスユーティリティ(`app/common/response_utils.py`)を使用してレスポンスを整形する

### 要件 7: エラーハンドリング

**目的:** ユーザーとして、パスワード変更処理の失敗時に適切なエラーメッセージを受け取りたい。なぜなら、何が起きたかを理解し、適切な対処ができるからだ。

#### 受け入れ基準

1. If データベースエラーが発生する, then the User API shall 500 Internal Server Error を返し、エラーをログに記録する
2. If 予期しない例外が発生する, then the User API shall 汎用的なエラーメッセージを返し、詳細をログに記録する
3. The User API shall 既存の共通エラーハンドラ(`app/common/error_handlers.py`)を使用してエラーレスポンスを整形する

### 要件 8: 監査ログ

**目的:** システム管理者として、パスワード変更操作を追跡したい。なぜなら、セキュリティ監査や問題調査のためだ。

#### 受け入れ基準

1. When パスワードが変更される, the User API shall 変更操作をログに記録する（ユーザーID、タイムスタンプ）
2. When パスワード変更が失敗する, the User API shall 失敗の詳細をログに記録する
3. The User API shall パスワードそのものをログに記録しない
