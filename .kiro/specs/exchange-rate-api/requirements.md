# Requirements Document

## Introduction
このドキュメントは、為替レート情報を取得するためのAPI（以下、為替レートAPI）の要件を定義します。
このAPIの主な目的は、海外のサブスクリプションサービスの料金をユーザーの選択した通貨に正確に変換し、フロントエンドで表示することです。これにより、ユーザーは支出を明確に把握できるようになります。

## Requirements

### Requirement 1: 為替レートの取得
**Objective:** `フロントエンドアプリケーション`として、`特定の日付と通貨ペアの為替レートを取得したい`。これにより、`ユーザーのサブスクリプション費用を正確に計算できる`。

#### Acceptance Criteria
1. `WHEN` `date`, `from_currency`, `to_currency` をクエリパラメータとして `/exchange-rates` へのGETリクエストが行われた `THEN` `為替レートAPI` `SHALL` 対応する為替レートを返す。
2. `IF` リクエストされた `date` の為替レートがデータベースに存在しない `THEN` `為替レートAPI` `SHALL` リクエストされた日付より前の直近のレートを返す。
3. `IF` リクエストされた `date` およびそれ以前の日付にレートが見つからない `THEN` `為替レートAPI` `SHALL` 404 Not Foundエラーを返す。
4. `IF` `date` パラメータが省略された `THEN` `為替レートAPI` `SHALL` 現在のサーバー日付をデフォルト値として使用する。
5. `IF` `from_currency` または `to_currency` パラメータが欠落している `THEN` `為替レートAPI` `SHALL` 400 Bad Requestエラーを返す。
6. `IF` `date` パラメータの形式が不正（例: YYYY-MM-DD以外）である `THEN` `為替レートAPI` `SHALL` 400 Bad Requestエラーを返す。