# Makefile for subsc-tracker-api (DevContainer / Local Environment)

.PHONY: help db-pull-prd run-repro run

# デフォルトのポート設定
PORT ?= 5000
REPRO_PORT ?= 5001

help:
	@echo "Available commands:"
	@echo "  make db-pull-prd  : Pull production database from GCS and save as instance/prd_repro.db"
	@echo "  make run-repro     : Run the application using the production database copy (Port: $(REPRO_PORT))"
	@echo "  make run           : Run the application normally (Port: $(PORT))"

db-pull-prd:
	@echo "Fetching production database copy (Directly from GCS using Litestream)..."
	@./scripts/dev/pull_prd_sqlite.sh instance/prd_repro.db

run-repro:
	@echo "Running application with production database copy on Port $(REPRO_PORT)..."
	@DB_NAME=instance/prd_repro.db poetry run flask --app 'app:create_app()' run --host=0.0.0.0 --port=$(REPRO_PORT) --debug

run:
	@echo "Running application normally on Port $(PORT)..."
	@poetry run flask --app 'app:create_app()' run --host=0.0.0.0 --port=$(PORT) --debug
