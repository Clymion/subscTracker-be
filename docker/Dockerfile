# ---- ビルダー・ステージ (Builder Stage) ----
FROM python:3.13-slim AS builder

# コマンドのユーティリティ
RUN echo "\\nalias ll='ls -la --color'\\n" >> /root/.bashrc

# 必要なパッケージをインストール
RUN apt-get update && apt-get install -y \
    git curl \
    && rm -rf /var/lib/apt/lists/*

# Poetry のインストールと設定
ENV POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_IN_PROJECT=false \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_CACHE_DIR=/tmp/poetry_cache

RUN curl -sSL https://install.python-poetry.org | python - \
    && chmod a+x /opt/poetry/bin/poetry

ENV PATH="$POETRY_HOME/bin:$PATH"

WORKDIR /workspace

# 依存関係をインストールする（開発用も含む）
COPY pyproject.toml poetry.lock* ./
# --only main は本番用、--with dev は開発用も含む
RUN poetry install --no-root

# ---- 本番ステージ (Production Stage) ----
# クリーンな環境に、ビルドした成果物だけをコピー
FROM python:3.13-slim AS production

# Litestreamのインストールに必要なパッケージを追加
RUN apt-get update && apt-get install -y curl ca-certificates && rm -rf /var/lib/apt/lists/*

# Litestreamをインストール
RUN curl -sfL "https://github.com/benbjohnson/litestream/releases/download/v0.3.12/litestream-v0.3.12-linux-amd64.deb" -o litestream.deb \
&& dpkg -i litestream.deb \
&& rm litestream.deb

WORKDIR /workspace

# ビルダー・ステージから、インストール済みのライブラリだけをコピー
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /workspace/pyproject.toml /workspace/pyproject.toml
COPY --from=builder /workspace/poetry.lock /workspace/poetry.lock

# アプリケーションコードをコピー
COPY . .
# Litestreamの設定ファイルをコピー
RUN mkdir -p /etc/litestream
COPY docker/litestream.yml /etc/litestream.yml

# データベースのディレクトリを作成
RUN mkdir -p /workspace/instance

# entrypointスクリプトをコピーして実行権限を付与
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

# Cloud Run は 8080 環境変数でリッスンするポートを指定
ENV PORT=8080

ENTRYPOINT ["./entrypoint.sh"]
