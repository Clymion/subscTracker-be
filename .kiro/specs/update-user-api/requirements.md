# Requirements Document

## Project Description (Input)
ユーザー情報更新API `PATCH {{host}}/api/v1/users/{{userId}}` の実装

## Introduction

本ドキュメントは、ユーザー情報更新APIの機能要件を定義する。このAPIは、認証済みユーザーが自身のプロフィール情報（ユーザー名、メールアドレス、基準通貨）を更新するためのものである。

## Requirements

### Requirement 1: ユーザー情報の更新機能
**Objective:** As a 認証済みユーザー, I want 自分のプロフィール情報を更新できる, so that アカウント情報を最新の状態に保つことができる

#### Acceptance Criteria
1. When 有効なJWTトークンを含むリクエストを受信したとき, the User Service shall ユーザーIDに対応するユーザーのプロフィール情報を更新する
2. When ユーザー名を含むリクエストを受信したとき, the User Service shall ユーザー名を3文字以上32文字以下の範囲で更新する
3. When メールアドレスを含むリクエストを受信したとき, the User Service shall 有効なメールフォーマットであることを検証し、重複がない場合に更新する
4. When 基準通貨を含むリクエストを受信したとき, the User Service shall JPY、USD、EUR、GBPのいずれかであることを検証し更新する
5. When 更新リクエストが正常に処理されたとき, the User Service shall 更新後のユーザー情報を含む成功レスポンスを返す

### Requirement 2: 認証・認可
**Objective:** As a システム管理者, I want 適切な認証・認可を強制できる, so that 不正なアクセスを防止しデータの安全性を確保できる

#### Acceptance Criteria
1. When JWTトークンなしでリクエストを受信したとき, the User Service shall 401 Unauthorizedエラーレスポンスを返す
2. When 他のユーザーのプロフィール更新リクエストを受信したとき, the User Service shall 403 Forbiddenエラーレスポンスを返す
3. When 存在しないユーザーIDでリクエストを受信したとき, the User Service shall 404 Not Foundエラーレスポンスを返す
4. The User Service shall リクエスト送信者のユーザーIDとパスパラメータのユーザーIDが一致することを検証する

### Requirement 3: バリデーション
**Objective:** As a システム管理者, I want 入力データのバリデーションを実施できる, so that データの整合性と品質を保証できる

#### Acceptance Criteria
1. When ユーザー名が3文字未満または32文字超のリクエストを受信したとき, the User Service shall 400 Bad Requestエラーレスポンスを返す
2. When 既に使用されているメールアドレスで更新リクエストを受信したとき, the User Service shall 400 Bad Requestエラーレスポンスを返す
3. When 無効な通貨コードで更新リクエストを受信したとき, the User Service shall 400 Bad Requestエラーレスポンスを返す
4. When 無効なメールフォーマットで更新リクエストを受信したとき, the User Service shall 400 Bad Requestエラーレスポンスを返す
5. When 空のリクエストボディを受信したとき, the User Service shall 400 Bad Requestエラーレスポンスを返す

### Requirement 4: 部分更新機能
**Objective:** As a ユーザー, I want 特定のフィールドのみを更新できる, so that 必要な情報だけを効率的に更新できる

#### Acceptance Criteria
1. When リクエストボディに一部のフィールドのみが含まれる場合, the User Service shall 指定されたフィールドのみを更新し、他のフィールドは変更せずに維持する
2. When 空のJSONオブジェクト`{}`を受信したとき, the User Service shall 400 Bad Requestエラーレスポンスを返す
3. When 複数のフィールドを含むリクエストを受信したとき, the User Service shall すべてのフィールドを原子的に更新する

### Requirement 5: レスポンス形式
**Objective:** As a APIクライアント開発者, I want 一貫したレスポンス形式を受け取れる, so that クライアントアプリケーションを効率的に開発できる

#### Acceptance Criteria
1. When 更新が正常に完了したとき, the User Service shall `data`フィールドに更新後のユーザー情報を含むJSONレスポンスを返す
2. When 更新が正常に完了したとき, the User Service shall HTTPステータスコード200を返す
3. When エラーが発生したとき, the User Service shall `error`フィールドにエラーコードとメッセージを含むJSONレスポンスを返す
4. The User Service shall レスポンスにユーザーID、ユーザー名、メールアドレス、基準通貨、作成日時を含める
