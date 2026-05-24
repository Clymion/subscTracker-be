# 検証・本番環境へのTiDB Cloud移行手順書

## 概要

本ドキュメントは、検証環境および本番環境のデータベースをSQLiteからTiDB Cloudへ移行するための手順書である。

## 前提条件

- Google Cloud プロジェクトで以下のAPIが有効になっていること
  - Cloud Build API
  - Cloud Run API
  - Artifact Registry API
  - Secret Manager API
- TiDB Cloudクラスターが作成済みであること（検証用・本番用）
- `gcloud` CLIがインストールされ、認証済みであること

---

## Phase 1: 事前準備

### 1.1 TiDB Cloud CA証明書の取得

1. TiDB Cloudコンソールにログイン
2. 対象のクラスターを選択
3. **Connect** > **Connect With** > **General** を選択
4. **CA Certificate** から証明書をダウンロード
5. プロジェクトの `credentials/tidb_ca.crt` として保存

```bash
# 証明書を配置
mkdir -p credentials
# ダウンロードした証明書を配置
# TiDB Cloudからダウンロードした isrgrootx1.pem をリネーム
cp ~/Downloads/isrgrootx1.pem credentials/tidb_ca.crt
```

### 1.2 TiDB Cloud接続情報の確認

TiDB Cloudコンソールから以下の情報を確認:

| 項目 | 説明 | 例 |
|------|------|-----|
| ホスト名 | `gateway01.<region>.prod.aws.tidbcloud.com` | `gateway01.ap-northeast-1.prod.aws.tidbcloud.com` |
| ポート | MySQL プロトコルポート | `4000` |
| ユーザー名 | 作成したユーザー | `xxxxxxxx.root` |
| パスワード | ユーザーのパスワード | （TiDB Cloudで設定した値） |
| データベース名 | 作成したデータベース | `subsc_tracker` |

### 1.3 ネットワーク確認

Cloud RunからTiDB Cloudへの接続（ポート4000）が可能か確認:

```bash
# ローカルから接続テスト
mysql -h gateway01.ap-northeast-1.prod.aws.tidbcloud.com \
      -P 4000 \
      -u 2m2DcRkJJsCk2p9.root \
      -p \
      --ssl-ca=credentials/tidb_ca.crt \
      -e "SELECT VERSION();"
```

---

## Phase 2: Secret Managerへの秘密情報登録

### 2.1 環境ごとの設定

検証環境と本番環境で異なるSecretを使用する場合、以下のようにプレフィックスを付けることを推奨:

- 検証環境: `STAGING_DB_HOST`, `STAGING_DB_PASSWORD` など
- 本番環境: `DB_HOST`, `DB_PASSWORD` など

### 2.2 Secretの作成

```bash
# プロジェクトIDを設定
PROJECT_ID="subscmanager"

# 本番環境用のSecretを作成
echo -n "gateway01.ap-northeast-1.prod.aws.tidbcloud.com" | \
  gcloud secrets create DB_HOST --data-file=- --project=$PROJECT_ID

echo -n "4000" | \
  gcloud secrets create DB_PORT --data-file=- --project=$PROJECT_ID

echo -n "2m2DcRkJJsCk2p9.root" | \
  gcloud secrets create DB_USER --data-file=- --project=$PROJECT_ID

echo -n "Iv7KF741xEgzS4yq" | \
  gcloud secrets create DB_PASSWORD --data-file=- --project=$PROJECT_ID

echo -n "subsc_tracker" | \
  gcloud secrets create DB_NAME --data-file=- --project=$PROJECT_ID
```

### 2.3 Secretへのアクセス権限設定

Cloud RunサービスアカウントにSecretへのアクセス権を付与:

```bash
# サービスアカウントのメールアドレスを取得
# SERVICE_ACCOUNT="subsc-tracker-backend@${PROJECT_ID}.iam.gserviceaccount.com"
SERVICE_ACCOUNT="1091250272813-compute@developer.gserviceaccount.com"

# 各Secretへのアクセス権を付与
for SECRET in DB_HOST DB_PORT DB_USER DB_PASSWORD DB_NAME; do
  gcloud secrets add-iam-policy-binding $SECRET \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/secretmanager.secretAccessor" \
    --project=$PROJECT_ID
done
```

---

## Phase 3: データ移行（メンテナンスウィンドウ内）

### 3.1 移行前バックアップ

```bash
# 本番SQLiteデータベースのバックアップ
BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
cp instance/app.db "instance/app.db.backup.$BACKUP_DATE"

# バックアップの確認
ls -la instance/app.db.backup.*
```

### 3.2 環境変数の設定

```bash
# 移行用環境変数を設定
export DB_DRIVER=mysql
export DB_HOST="gateway01.ap-northeast-1.prod.aws.tidbcloud.com"
export DB_PORT=4000
export DB_USER="2m2DcRkJJsCk2p9.root"
export DB_PASSWORD="Iv7KF741xEgzS4yq"
export DB_NAME="subsc_tracker"
export DB_SSL_CA="$(pwd)/credentials/tidb_ca.crt"
export JWT_SECRET_KEY="temporary_key_for_migration"
```

### 3.3 スキーマ移行

```bash
# Alembicマイグレーションを実行
python -m alembic upgrade head

# テーブル作成の確認
mysql -h $DB_HOST -P $DB_PORT -u $DB_USER -p$DB_PASSWORD \
      --ssl-ca=$DB_SSL_CA $DB_NAME -e "SHOW TABLES;"
```

### 3.4 データ移行

```bash
# データ移行スクリプトを実行
python scripts/migrate_data.py \
  --source instance/prd_repro.db \
  --dest "mysql+pymysql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}" \
  --ssl-ca credentials/tidb_ca.crt \
  --checkpoint .migration_checkpoint.json \
  --batch-size 1000
```

### 3.5 データ整合性検証

```bash
# 行数の比較
echo "=== SQLite Row Counts ==="
sqlite3 instance/app.db "SELECT 'users', COUNT(*) FROM users UNION ALL SELECT 'subscriptions', COUNT(*) FROM subscriptions UNION ALL SELECT 'labels', COUNT(*) FROM labels UNION ALL SELECT 'payment_histories', COUNT(*) FROM payment_histories;"

echo "=== TiDB Row Counts ==="
mysql -h $DB_HOST -P $DB_PORT -u $DB_USER -p$DB_PASSWORD \
      --ssl-ca=$DB_SSL_CA $DB_NAME \
      -e "SELECT 'users', COUNT(*) FROM users UNION ALL SELECT 'subscriptions', COUNT(*) FROM subscriptions UNION ALL SELECT 'labels', COUNT(*) FROM labels UNION ALL SELECT 'payment_histories', COUNT(*) FROM payment_histories;"

# 外部キー整合性チェック
mysql -h $DB_HOST -P $DB_PORT -u $DB_USER -p$DB_PASSWORD \
      --ssl-ca=$DB_SSL_CA $DB_NAME \
      -e "
        SELECT 'orphaned_subscriptions', COUNT(*) FROM subscriptions s
        LEFT JOIN users u ON s.user_id = u.user_id
        WHERE u.user_id IS NULL;
      "
```

---

## Phase 4: デプロイ

### 4.1 検証環境へのデプロイ

```bash
# 検証環境用のcloudbuild.yamlを使用するか、変数を変更してデプロイ
gcloud builds submit --config=cloudbuild.yaml . \
  --substitutions=_SERVICE_NAME="subsc-tracker-backend-staging"
```

### 4.2 検証環境の動作確認

```bash
# ヘルスチェック
curl https://staging-api.example.com/api/v1/system/health

# API動作確認
curl -X POST https://staging-api.example.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "test_password"}'
```

### 4.3 本番環境へのデプロイ

```bash
# メンテナンスモードを有効にする（必要に応じて）

# デプロイ実行
./deploy.sh

# または直接Cloud Buildを実行
gcloud builds submit --config=cloudbuild.yaml .
```

### 4.4 本番環境の動作確認

```bash
# ヘルスチェック
curl https://api.example.com/api/v1/system/health

# 期待されるレスポンス
# {"status": "healthy", "checks": {"database": "healthy"}}
```

---

## Phase 5: 移行後の確認

### 5.1 アプリケーションログの確認

```bash
# Cloud Runのログを確認
gcloud run logs read --service=subsc-tracker-backend --limit=100
```

### 5.2 データベース接続の監視

```bash
# 接続数の確認
mysql -h $DB_HOST -P $DB_PORT -u $DB_USER -p$DB_PASSWORD \
      --ssl-ca=$DB_SSL_CA $DB_NAME \
      -e "SHOW PROCESSLIST;"
```

### 5.3 パフォーマンス確認

- APIのレスポンスタイムを確認
- Cloud Runのコンテナリソース使用率を確認
- 必要に応じて接続プール設定を調整

---

## ロールバック手順

### 即時ロールバック（アプリケーション）

```bash
# 前のリビジョンに戻す
gcloud run services update-traffic subsc-tracker-backend \
  --to-revisions PREVIOUS_REVISION=100

# リビジョン一覧を確認
gcloud run revisions list --service=subsc-tracker-backend
```

### データロールバック

移行後に重大な問題が発生した場合:

1. **アプリケーションを停止**
   ```bash
   gcloud run services update subsc-tracker-backend --min-instances=0
   ```

2. **SQLiteバックアップから復元**
   - Cloud Runの環境変数をSQLiteに戻す
   - 前のバージョンのコンテナをデプロイ

3. **TiDB CloudのPoint-in-Time Recovery**
   - TiDB CloudコンソールからPITRを実行（サポートが必要な場合）

---

## チェックリスト

### 事前準備

- [x] TiDB Cloudクラスターが作成済み
- [x] CA証明書が `credentials/tidb_ca.crt` に配置済み
- [x] Secret Managerに全てのSecretが登録済み
- [x] サービスアカウントにSecretアクセス権が付与済み
- [x] ネットワーク接続が確認済み

### データ移行

- [x] SQLiteバックアップが作成済み
- [x] スキーマ移行が完了
- [x] データ移行が完了
- [x] データ整合性が検証済み

### デプロイ

- [x] 検証環境での動作確認が完了
- [x] 本番環境へのデプロイが完了
- [x] ヘルスチェックが成功
- [x] API動作確認が完了

---

## 参照

- [TiDB Cloud Documentation](https://docs.pingcap.com/tidbcloud/)
- [Google Cloud Secret Manager](https://cloud.google.com/secret-manager/docs)
- [Cloud Run Documentation](https://cloud.google.com/run/docs)
