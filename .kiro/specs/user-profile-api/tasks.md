# Implementation Plan

## Task Format Template

Use whichever pattern fits the work breakdown:

### Major task only
- [ ] {{NUMBER}}. {{TASK_DESCRIPTION}}{{PARALLEL_MARK}}
  - {{DETAIL_ITEM_1}} *(Include details only when needed. If the task stands alone, omit bullet items.)*
  - _Requirements: {{REQUIREMENT_IDS}}_

### Major + Sub-task structure
- [ ] {{MAJOR_NUMBER}}. {{MAJOR_TASK_SUMMARY}}
- [ ] {{MAJOR_NUMBER}}.{{SUB_NUMBER}} {{SUB_TASK_DESCRIPTION}}{{SUB_PARALLEL_MARK}}
  - {{DETAIL_ITEM_1}}
  - {{DETAIL_ITEM_2}}
  - _Requirements: {{REQUIREMENT_IDS}}_ *(IDs only; do not add descriptions or parentheses.)*

> **Parallel marker**: Append ` (P)` only to tasks that can be executed in parallel. Omit the marker when running in `--sequential` mode.
>
> **Optional test coverage**: When a sub-task is deferrable test work tied to acceptance criteria, mark the checkbox as `- [ ]*` and explain the referenced requirements in the detail bullets.

---

## Tasks

- [x] 1. プロフィール取得APIの統合テストを作成する
- [x] 1.1 認証済みユーザーが自分のプロフィールを取得できることを検証する
  - 有効なJWTトークンでGET /api/v1/users/{userId}を呼び出す
  - レスポンスがユーザーID、ユーザー名、メールアドレス、基準通貨、作成日時を含むことを確認
  - レスポンス形式が`data`フィールドを持つことを確認
  - _Requirements: 1.1, 4.1_

- [x] 1.2 未認証ユーザーが401エラーを受け取ることを検証する
  - JWTトークンなしでGET /api/v1/users/{userId}を呼び出す
  - レスポンスが401ステータスコードであることを確認
  - エラーレスポンスが`error`フィールドを持つことを確認
  - _Requirements: 1.2, 4.2_

- [x] 1.3 他のユーザーのプロフィール取得で403エラーになることを検証する
  - ユーザーAのトークンでユーザーBのプロフィールを取得しようとする
  - レスポンスが403ステータスコードであることを確認
  - _Requirements: 1.3_

- [x] 1.4 存在しないユーザーIDで404エラーになることを検証する
  - 存在しないユーザーIDでGET /api/v1/users/{userId}を呼び出す
  - レスポンスが404ステータスコードであることを確認
  - _Requirements: 1.4_

- [x] 2. プロフィール更新APIの統合テストを作成する
- [x] 2.1 (P) ユーザー名の更新を検証する
  - 有効なユーザー名（3-32文字）でPATCH /api/v1/users/{userId}を呼び出す
  - 更新後のユーザー名がレスポンスに反映されることを確認
  - _Requirements: 2.1, 2.2_

- [x] 2.2 (P) メールアドレスの更新を検証する
  - 有効なメールフォーマットでPATCH /api/v1/users/{userId}を呼び出す
  - 更新後のメールアドレスがレスポンスに反映されることを確認
  - _Requirements: 2.1, 2.3_

- [x] 2.3 (P) 基準通貨の更新を検証する
  - 有効な通貨コード（JPY, USD, EUR, GBP）で更新
  - 更新が正常に行われることを確認
  - _Requirements: 2.1, 2.4_

- [x] 2.4 メール重複で400エラーになることを検証する
  - 既に使用されているメールアドレスに更新しようとする
  - レスポンスが400ステータスコードであることを確認
  - _Requirements: 2.5_

- [x] 2.5 無効な通貨コードで400エラーになることを検証する
  - 無効な通貨コード（例: "XYZ"）で更新しようとする
  - レスポンスが400ステータスコードであることを確認
  - _Requirements: 2.6_

- [x] 2.6 未認証ユーザーが更新で401エラーになることを検証する
  - JWTトークンなしでPATCH /api/v1/users/{userId}を呼び出す
  - レスポンスが401ステータスコードであることを確認
  - _Requirements: 2.7, 4.2_

- [x] 2.7 他ユーザーのプロフィール更新で403エラーになることを検証する
  - ユーザーAのトークンでユーザーBのプロフィールを更新しようとする
  - レスポンスが403ステータスコードであることを確認
  - _Requirements: 2.8_

- [x] 2.8 空のリクエストボディで400エラーになることを検証する
  - 空のJSONでPATCHリクエストを送信する
  - レスポンスが400ステータスコードであることを確認
  - _Requirements: 2.9_

- [x] 3. 部分更新機能の統合テストを作成する
- [x] 3.1 一部フィールドのみの更新を検証する
  - ユーザー名のみを更新し、他のフィールドが変更されないことを確認
  - メールアドレスのみを更新し、他のフィールドが変更されないことを確認
  - _Requirements: 3.1_

- [x] 3.2 空のオブジェクトでプロフィールが変更されないことを検証する
  - 空のJSONオブジェクト`{}`でPATCHリクエストを送信する
  - 現在のプロフィール情報が変更されずに返されることを確認
  - _Requirements: 3.2_
