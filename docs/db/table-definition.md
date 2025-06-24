# テーブル定義書

## 目次

- [テーブル定義書](#テーブル定義書)
  - [目次](#目次)
  - [テーブル一覧](#テーブル一覧)
  - [テーブル定義](#テーブル定義)
    - [USERS（ユーザー）](#usersユーザー)
    - [SUBSCRIPTIONS（サブスクリプション）](#subscriptionsサブスクリプション)
    - [PAYMENT\_HISTORY（支払い履歴）](#payment_history支払い履歴)
    - [EXCHANGE\_RATES（為替レート）](#exchange_rates為替レート)
    - [NOTIFICATIONS（通知）](#notifications通知)
    - [LABELS（ラベル）](#labelsラベル)
    - [SUBSCRIPTION\_LABELS（サブスクリプションラベル）](#subscription_labelsサブスクリプションラベル)
    - [CURRENCY\_SETTINGS（通貨設定）](#currency_settings通貨設定)
  - [インデックス定義](#インデックス定義)
    - [SUBSCRIPTIONS テーブル](#subscriptions-テーブル)
    - [LABELS テーブル](#labels-テーブル)
    - [PAYMENT\_HISTORY テーブル](#payment_history-テーブル)
    - [NOTIFICATIONS テーブル](#notifications-テーブル)
    - [外部キー制約](#外部キー制約)

## テーブル一覧

| テーブル物理名 | テーブル論理名 | 説明 |
|--------------|--------------|------|
| USERS | ユーザー | ユーザー情報を管理するテーブル |
| SUBSCRIPTIONS | サブスクリプション | サブスクリプションサービスの情報を管理するテーブル |
| PAYMENT_HISTORY | 支払い履歴 | サブスクリプションの支払い履歴を管理するテーブル |
| EXCHANGE_RATES | 為替レート | 通貨間の為替レートを管理するテーブル |
| NOTIFICATIONS | 通知 | ユーザーへの通知情報を管理するテーブル |
| LABELS | ラベル | サブスクリプション分類用のラベルを管理するテーブル（階層構造対応） |
| SUBSCRIPTION_LABELS | サブスクリプションラベル | サブスクリプションとラベルの関連を管理するテーブル |
| CURRENCY_SETTINGS | 通貨設定 | ユーザーごとの基準通貨設定を管理するテーブル |

## テーブル定義

### USERS（ユーザー）

| 物理名 | 論理名 | データ型 | PK | FK | NOT NULL | 制約 | 説明 | 備考 |
|--------|--------|----------|-----|-----|----------|------|------|------|
| user_id | ユーザーID | INT | O | - | O | AUTO_INCREMENT | ユーザーを一意に識別するID | - |
| username | ユーザー名 | STRING | - | - | O | UNIQUE | ユーザーのログイン名 | - |
| password_hash | パスワードハッシュ | STRING | - | - | O | - | ハッシュ化されたパスワード | - |
| email | メールアドレス | STRING | - | - | O | UNIQUE | ユーザーのメールアドレス | - |
| created_at | 作成日時 | TIMESTAMP | - | - | O | - | レコード作成日時 | - |
| updated_at | 更新日時 | TIMESTAMP | - | - | O | - | レコード更新日時 | - |

### SUBSCRIPTIONS（サブスクリプション）

| 物理名 | 論理名 | データ型 | PK | FK | NOT NULL | 制約 | 説明 | 備考 |
|--------|--------|----------|-----|-----|----------|------|------|------|
| subscription_id | サブスクリプションID | INT | O | - | O | AUTO_INCREMENT | サブスクリプションを一意に識別するID | - |
| user_id | ユーザーID | INT | - | O | O | - | 所有ユーザーのID | USERS.user_id参照 |
| name | サービス名 | STRING | - | - | O | - | サブスクリプションサービスの名称 | - |
| price | 料金 | REAL | - | - | O | - | サービスの料金 | SQLite REAL型 |
| currency | 通貨 | STRING | - | - | O | - | 料金の通貨 | USD または JPY のみ |
| initial_payment_date | 初回支払日 | DATE | - | - | O | - | サービスの初回支払日 | - |
| next_payment_date | 次回支払日 | DATE | - | - | O | - | サービスの次回支払予定日 | - |
| payment_frequency | 支払頻度 | STRING | - | - | O | - | 支払いの頻度 | monthly/yearly等 |
| payment_method | 支払方法 | STRING | - | - | O | - | 支払いの方法 | - |
| status | ステータス | STRING | - | - | O | - | サブスクリプションの状態 | trial/active等 |
| url | URL | STRING | - | - | - | - | サービスのURL | - |
| notes | メモ | TEXT | - | - | - | - | 備考欄 | - |
| image_url | 画像URL | STRING | - | - | - | - | サービスのロゴ等の画像URL | - |
| created_at | 作成日時 | TIMESTAMP | - | - | O | - | レコード作成日時 | - |
| updated_at | 更新日時 | TIMESTAMP | - | - | O | - | レコード更新日時 | - |

### PAYMENT_HISTORY（支払い履歴）

| 物理名 | 論理名 | データ型 | PK | FK | NOT NULL | 制約 | 説明 | 備考 |
|--------|--------|----------|-----|-----|----------|------|------|------|
| payment_id | 支払いID | INT | O | - | O | AUTO_INCREMENT | 支払いを一意に識別するID | - |
| subscription_id | サブスクリプションID | INT | - | O | O | - | 支払い対象のサブスクリプションID | SUBSCRIPTIONS.subscription_id参照 |
| amount | 支払額 | INT | - | - | O | - | 支払い金額 | - |
| currency | 通貨 | STRING | - | - | O | - | 支払い通貨 | USD または JPY |
| rate_id | レートID | INT | - | O | O | - | 適用された為替レートのID | EXCHANGE_RATES.rate_id参照 |
| payment_method | 支払方法 | STRING | - | - | O | - | 実際の支払方法 | - |
| payment_date | 支払日 | DATE | - | - | O | - | 実際の支払日 | - |
| created_by | 作成者 | INT | - | O | O | - | レコード作成者のID | USERS.user_id参照 |
| created_at | 作成日時 | TIMESTAMP | - | - | O | - | レコード作成日時 | - |
| updated_by | 更新者 | INT | - | O | O | - | レコード更新者のID | USERS.user_id参照 |
| updated_at | 更新日時 | TIMESTAMP | - | - | O | - | レコード更新日時 | - |

### EXCHANGE_RATES（為替レート）

| 物理名 | 論理名 | データ型 | PK | FK | NOT NULL | 制約 | 説明 | 備考 |
|--------|--------|----------|-----|-----|----------|------|------|------|
| rate_id | レートID | INT | O | - | O | AUTO_INCREMENT | 為替レートを一意に識別するID | - |
| from_currency | 変換元通貨 | STRING | - | - | O | - | 変換元の通貨コード | USD または JPY |
| to_currency | 変換先通貨 | STRING | - | - | O | - | 変換先の通貨コード | USD または JPY |
| rate | レート | REAL | - | - | O | - | 為替レート | - |
| source | データソース | STRING | - | - | O | - | レート取得元 | - |
| date | 基準日 | DATE | - | - | O | - | レートの基準日 | - |
| created_at | 作成日時 | TIMESTAMP | - | - | O | - | レコード作成日時 | - |
| updated_at | 更新日時 | TIMESTAMP | - | - | O | - | レコード更新日時 | - |

### NOTIFICATIONS（通知）

| 物理名 | 論理名 | データ型 | PK | FK | NOT NULL | 制約 | 説明 | 備考 |
|--------|--------|----------|-----|-----|----------|------|------|------|
| notification_id | 通知ID | INT | O | - | O | AUTO_INCREMENT | 通知を一意に識別するID | - |
| user_id | ユーザーID | INT | - | O | O | - | 通知対象ユーザーのID | USERS.user_id参照 |
| subscription_id | サブスクリプションID | INT | - | O | - | - | 関連するサブスクリプションID | SUBSCRIPTIONS.subscription_id参照 |
| message | メッセージ | STRING | - | - | O | - | 通知内容 | - |
| read_status | 既読状態 | BOOLEAN | - | - | O | - | 通知の既読状態 | - |
| created_at | 作成日時 | TIMESTAMP | - | - | O | - | レコード作成日時 | - |
| updated_at | 更新日時 | TIMESTAMP | - | - | O | - | レコード更新日時 | - |

### LABELS（ラベル）

| 物理名 | 論理名 | データ型 | PK | FK | NOT NULL | 制約 | 説明 | 備考 |
|--------|--------|----------|-----|-----|----------|------|------|------|
| label_id | ラベルID | INT | O | - | O | AUTO_INCREMENT | ラベルを一意に識別するID | - |
| user_id | ユーザーID | INT | - | O | O | - | ラベル作成者のID | USERS.user_id参照 |
| parent_id | 親ラベルID | INT | - | O | - | - | 親ラベルのID（階層構造） | LABELS.label_id参照 |
| name | ラベル名 | STRING | - | - | O | - | ラベルの名称 | - |
| color | 色 | STRING | - | - | O | - | ラベルの表示色 | HEXカラーコード |
| system_label | システムラベル | BOOLEAN | - | - | O | DEFAULT FALSE | システム提供ラベルフラグ | デフォルトラベル判定用 |
| created_at | 作成日時 | TIMESTAMP | - | - | O | - | レコード作成日時 | - |
| updated_at | 更新日時 | TIMESTAMP | - | - | O | - | レコード更新日時 | - |

### SUBSCRIPTION_LABELS（サブスクリプションラベル）

| 物理名 | 論理名 | データ型 | PK | FK | NOT NULL | 制約 | 説明 | 備考 |
|--------|--------|----------|-----|-----|----------|------|------|------|
| subscription_id | サブスクリプションID | INT | O | O | O | - | サブスクリプションID | SUBSCRIPTIONS.subscription_id参照 |
| label_id | ラベルID | INT | O | O | O | - | ラベルID | LABELS.label_id参照 |

### CURRENCY_SETTINGS（通貨設定）

| 物理名 | 論理名 | データ型 | PK | FK | NOT NULL | 制約 | 説明 | 備考 |
|--------|--------|----------|-----|-----|----------|------|------|------|
| user_id | ユーザーID | INT | O | O | O | - | 設定対象ユーザーのID | USERS.user_id参照 |
| base_currency | 基準通貨 | STRING | - | - | O | - | ユーザーの基準通貨 | USD または JPY |
| created_at | 作成日時 | TIMESTAMP | - | - | O | - | レコード作成日時 | - |
| updated_at | 更新日時 | TIMESTAMP | - | - | O | - | レコード更新日時 | - |

## インデックス定義

### SUBSCRIPTIONS テーブル

| インデックス名 | 対象カラム | タイプ | 説明 |
|--------------|-----------|-------|------|
| idx_subscriptions_user_id | user_id | BTREE | ユーザー別のサブスクリプション検索用 |
| idx_subscriptions_status | status | BTREE | ステータスフィルタリング用 |
| idx_subscriptions_currency | currency | BTREE | 通貨フィルタリング用 |
| idx_subscriptions_user_status | user_id, status | BTREE | ユーザー×ステータス複合検索用 |
| idx_subscriptions_pagination | user_id, created_at | BTREE | ページネーション用（作成日時順） |
| idx_subscriptions_pagination_name | user_id, name | BTREE | ページネーション用（名前順） |
| idx_subscriptions_pagination_price | user_id, price | BTREE | ページネーション用（価格順） |

### LABELS テーブル

| インデックス名 | 対象カラム | タイプ | 説明 |
|--------------|-----------|-------|------|
| idx_labels_user_id | user_id | BTREE | ユーザー別のラベル検索用 |
| idx_labels_parent_id | parent_id | BTREE | 階層構造検索用 |
| idx_labels_user_parent | user_id, parent_id | BTREE | ユーザー×親ラベル複合検索用 |
| idx_labels_system | system_label | BTREE | システムラベル検索用 |

### PAYMENT_HISTORY テーブル

| インデックス名 | 対象カラム | タイプ | 説明 |
|--------------|-----------|-------|------|
| idx_payment_subscription_id | subscription_id | BTREE | サブスクリプション別支払い履歴検索用 |
| idx_payment_date | payment_date | BTREE | 支払い日による検索用 |
| idx_payment_pagination | subscription_id, payment_date | BTREE | ページネーション用（支払い日時順） |

### NOTIFICATIONS テーブル

| インデックス名 | 対象カラム | タイプ | 説明 |
|--------------|-----------|-------|------|
| idx_notifications_user_id | user_id | BTREE | ユーザー別通知検索用 |
| idx_notifications_read_status | read_status | BTREE | 既読・未読フィルタリング用 |
| idx_notifications_pagination | user_id, created_at | BTREE | ページネーション用（作成日時順） |

### 外部キー制約

| テーブル | 外部キー | 参照テーブル | 参照カラム | 削除時動作 |
|---------|---------|------------|----------|----------|
| SUBSCRIPTIONS | user_id | USERS | user_id | CASCADE |
| PAYMENT_HISTORY | subscription_id | SUBSCRIPTIONS | subscription_id | CASCADE |
| PAYMENT_HISTORY | created_by | USERS | user_id | RESTRICT |
| PAYMENT_HISTORY | updated_by | USERS | user_id | RESTRICT |
| PAYMENT_HISTORY | rate_id | EXCHANGE_RATES | rate_id | RESTRICT |
| NOTIFICATIONS | user_id | USERS | user_id | CASCADE |
| NOTIFICATIONS | subscription_id | SUBSCRIPTIONS | subscription_id | CASCADE |
| LABELS | user_id | USERS | user_id | CASCADE |
| LABELS | parent_id | LABELS | label_id | CASCADE |
| SUBSCRIPTION_LABELS | subscription_id | SUBSCRIPTIONS | subscription_id | CASCADE |
| SUBSCRIPTION_LABELS | label_id | LABELS | label_id | CASCADE |
| CURRENCY_SETTINGS | user_id | USERS | user_id | CASCADE |
