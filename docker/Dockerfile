FROM python:3.13-slim

ARG WORKSPACE_FOLDER

RUN echo "\\nalias ll='ls -la --color'\\n" >> /root/.bashrc

# 必要なパッケージをインストール
RUN apt-get update && apt-get install -y \
    git curl procps \
    && rm -rf /var/lib/apt/lists/*

# Poetry のインストール
ENV POETRY_HOME="/opt/poetry" \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=false \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_INSTALLER_PARALLEL=false \
    POETRY_CACHE_DIR=/tmp/poetry_cache

RUN curl -sSL https://install.python-poetry.org | python - \
    && chmod a+x /opt/poetry/bin/poetry

ENV PATH="$POETRY_HOME/bin:$PATH"

# 作業ディレクトリを作成
RUN mkdir -p ${WORKSPACE_FOLDER}

WORKDIR ${WORKSPACE_FOLDER}

# poetryの設定とインストール
COPY pyproject.toml poetry.lock* ./
RUN poetry config virtualenvs.in-project false \
    && poetry config installer.parallel false \
    && poetry config virtualenvs.create false \
    && poetry install --no-root

USER root

# Pythonのパスを設定
ENV PYTHONPATH=${WORKSPACE_FOLDER}

# Flaskアプリが使用するポートを公開
EXPOSE 5000

# 開発サーバー起動コマンド
# CMD ["flask", "--app", "api", "run", "--host=0.0.0.0"]
