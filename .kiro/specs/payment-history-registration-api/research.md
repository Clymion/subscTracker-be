# 実装ギャップ分析レポート

## 1. 概要
このドキュメントは `payment-history-registration-api` 機能の要求仕様を満たすために、既存のコードベースに対してどのような追加・修正が必要になるかのギャップを分析し、実装戦略を提案するものです。

## 2. 分析結果サマリー
調査の結果、支払い履歴を登録する機能の大部分は、既存のコンポーネント（リポジトリ、為替レートサービスなど）を組み合わせることで実装可能です。中心的なギャップは、APIエンドポイントそのものと、複数のサービスを協調させるビジネスロジックの不在です。

- **不足している主要コンポーネント**:
  - `POST /api/v1/payments` のAPIエンドポイント
  - 支払い履歴作成のビジネスロジックを集約するサービスメソッド

- **活用可能な既存コンポーネント**:
  - `PaymentHistoryRepository` の `save` メソッド
  - `ExchangeRateService` の `get_exchange_rate` メソッド
  - `User` モデルの `base_currency` 属性
  - JWTベースの認証デコレーター

## 3. 要求事項ごとのギャップ分析

### 要求事項1：支払履歴登録APIエンドポイント

- **現状**: `app/api/v1/payment_history.py` には `GET /payments` エンドポイントのみが存在し、`POST` は未実装です。
- **ギャップ**: `POST /api/v1/payments` を処理するルート関数が完全に欠落しています。
- **対応方針**:
  - `payment_history.py` 内の既存のBlueprint `payment_history_bp` を使用し、`@payment_history_bp.route("/payments", methods=["POST"])` のデコレーターを持つ新しい関数 `create_payment` を追加します。
  - この関数は `@jwt_required()` で保護し、`get_jwt_identity()` でユーザーIDを取得します。
  - リクエストボディは、OpenAPI定義に沿ったスキーマ（例: Marshmallow）でバリデーションを行います。
  - バリデーション後、`PaymentHistoryService` の新しいメソッド（`create_payment`）を呼び出します。
  - サービス層から返却された結果や例外に基づき、適切なHTTPステータスコード（201, 400, 401, 403, 404）を返します。

### 要求事項2：支払履歴データの保存

- **現状**:
  - `app/services/payment_history_service.py` には `get_payment_history` メソッドのみ存在します。
  - `app/repositories/payment_history_repository.py` には汎用的な `save(payment_history)` メソッドが存在します。
- **ギャップ**: `PaymentHistoryService` に、支払い履歴を作成するためのビジネスロジックを集約するメソッドがありません。
- **対応方針**:
  - `PaymentHistoryService` に `create_payment(self, user_id: int, payment_data: dict)` という新しいメソッドを追加します。
  - このメソッド内で以下の処理を実行します。
    1. `subscription_repository` を使用して、`payment_data['subscription_id']` が存在し、かつ `user_id` に紐付いていることを検証します（403/404エラーハンドリング）。
    2. `PaymentHistory` モデルのインスタンスを生成します。
    3. `payment_history_repository.save()` を呼び出して永続化します。
    4. 作成されたオブジェクトをAPI層に返します。

### 要求事項3：為替レートの自動計算と保存

- **現状**:
  - `app/services/exchange_rate_service.py` に `get_exchange_rate(target_date, from_currency, to_currency)` メソッドが存在します。
  - `app/models/user.py` に `base_currency` 属性が存在します。
- **ギャップ**: 支払い履歴作成のロジック内で、為替レート計算を組み込む処理がありません。
- **対応方針**:
  - `PaymentHistoryService` の `create_payment` メソッド内で、このロジックを実装します。
  - `user_repository` を使ってユーザー情報を取得し、`base_currency` を特定します。
  - リクエストの `currency` と `base_currency` が異なる場合、`ExchangeRateService` のインスタンスを介して `get_exchange_rate` を呼び出します。
  - 取得したレートを用いて `converted_amount` を計算します。
  - レートが見つからない場合、要求仕様通り `400 Bad Request` につながる例外を発生させます。
  - `PaymentHistory` インスタンスに `exchange_rate` と `converted_amount` を設定してから保存します。

## 4. 実装戦略の提案

上記分析に基づき、以下のステップで実装を進めることを提案します。

1. **サービス層の拡張**:
   - `PaymentHistoryService` のコンストラクタを修正し、`ExchangeRateService`, `SubscriptionRepository`, `UserRepository` を依存性注入（DI）できるようにします。
   - `create_payment` メソッドを `PaymentHistoryService` に実装し、前述のビジネスロジック（権限検証、為替計算、永続化）をすべて集約します。

2. **API層の実装**:
   - `app/api/v1/payment_history.py` に `POST /payments` のルートと `create_payment` 関数を追加します。
   . この関数はリクエストの検証と、`PaymentHistoryService.create_payment` の呼び出し、レスポンスの整形に責務を限定します。

このアプローチにより、関心の分離が保たれ、テスト容易性の高いコードを維持できます。
