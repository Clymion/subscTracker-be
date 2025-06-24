#!/bin/bash
# 本番環境へのデプロイを実行するスクリプト

# 前提条件
## Google Cloudにログインしていること。 (gcloud auth login コマンドでログインできていること）
## Google Cloudプロジェクトで Cloud Build API, Cloud Run API, Artifact Registry API が有効になっていること。
## deploy.sh と cloudbuild.yaml の変数（プロジェクトID、サービス名など）が正しく設定されていること。
## （推奨）本番用の秘密情報は、Google CloudのSecret Managerに登録済みであること。

# --- 設定項目 (あなたの環境に合わせて変更) ---

## Google Cloud プロジェクトID
PROJECT_ID="subscmanager"

## Artifact Registry のリポジトリ名
ARTIFACT_REPO_NAME="subsc-tracker-repo"

## コンテナイメージ名
IMAGE_NAME="subsc-tracker-api"

## Cloud Run のサービス名
SERVICE_NAME="subsc-tracker-backend"

## デプロイするリージョン
REGION="asia-northeast1"

# --- スクリプト本体 ---

# コマンドが失敗したら、すぐにスクリプトを終了する
set -e

echo "🚀 デプロイを開始"
echo "----------------------------------------"
echo "PROJECT_ID: $PROJECT_ID"
echo "SERVICE_NAME: $SERVICE_NAME"
echo "REGION: $REGION"
echo "----------------------------------------"

# gcloudコマンドが使えるかチェック
if ! command -v gcloud &> /dev/null
then
    echo "🚨 gcloud コマンドが見つからない。インストールしてパスを通してください。"
    exit 1
fi

# 認証とプロジェクト設定の確認
echo "gcloudの認証とプロジェクト設定を確認..."
gcloud auth list
gcloud config set project "$PROJECT_ID"
echo "✅ 確認完了"

TAG="manual-$(date +%Y%m%d-%H%M%S)"
echo "🏷️ 今回のビルドタグ: $TAG"

# Cloud Build を使って、イメージのビルドとデプロイを実行
# cloudbuild.yaml に定義されたステップが実行される
echo "🛠️ Cloud Build を使ってビルドとデプロイを実行中..."
gcloud builds submit --config cloudbuild.yaml . \
  --substitutions=_SERVICE_NAME="$SERVICE_NAME",_REGION="$REGION",_ARTIFACT_REPO_NAME="$ARTIFACT_REPO_NAME",_IMAGE_NAME="$IMAGE_NAME",COMMIT_SHA="$TAG"

echo "🎉 デプロイが正常に完了"
