# Implementation Gap Analysis

## 概要

本ドキュメントは、SQLiteからTiDBへの移行要件と既存コードベースのギャップを分析する。

## 1. 現状調査

### 1.1 既存アセット

| コンポーネント | ファイル | 現状 |
|--------------|---------|------|
| データベース設定 | `app/config.py` | `DB_DRIVER`環境変数で`sqlite`/`mysql`をサポート |
| モデル初期化 | `app/models/__init__.py` | SQLite PRAGMA設定（外部キー制約） |
| マイグレーション | `migrations/env.py` | 環境変数から接続URL取得、Alembic使用 |
| Docker構成 | `compose.yml` | **TiDBコンテナ既に設定済み** |
| 依存関係 | `pyproject.toml` | `pymysql`パッケージ既に追加済み |
| テスト設定 | `tests/conftest.py` | インメモリSQLite使用 |
| リポジトリ | `app/repositories/payment_history_repository.py` | SQLite固有のバルク操作回避ロジック |

### 1.2 既存パターンと規約

- **レイヤードアーキテクチャ**: API → Service → Repository
- **設定管理**: pydantic-settingsによる環境変数管理
- **ORM**: SQLAlchemy + Flask-SQLAlchemy
- **マイグレーション**: Alembic（自動生成対応）
- **テスト**: pytest + フィクスチャパターン

### 1.3 統合ポイント

```
┌─────────────────────────────────────────────────────────────┐
│                     Application Layer                        │
├─────────────────────────────────────────────────────────────┤
│  config.py ──> database_url ──> SQLAlchemy Engine           │
│      │                                                       │
│      └── DB_DRIVER: sqlite | mysql (tidb未対応)             │
├─────────────────────────────────────────────────────────────┤
│  models/__init__.py ──> SQLite PRAGMA (条件分岐なし)        │
├─────────────────────────────────────────────────────────────┤
│  migrations/env.py ──> DATABASE_URL (動的取得済み)          │
├─────────────────────────────────────────────────────────────┤
│  compose.yml ──> TiDB container (既に設定済み)              │
└─────────────────────────────────────────────────────────────┘
```

## 2. 要件実現可能性分析

### Requirement-to-Asset Map

| 要件 | 既存資産 | ギャップ | 影響度 |
|-----|---------|---------|-------|
| **1. DB接続設定** | `config.py`でmysql対応済み | `tidb`ドライバー未対応、SSL設定不足 | 低 |
| **2. SQLite固有コード** | PRAGMA設定あり | 条件分岐なし | 低 |
| **3. スキーマ互換性** | SQLAlchemyモデル定義 | 複合主キーのTiDB検証必要 | 中 |
| **4. マイグレーション** | Alembic設定済み | Dialect違いの確認 | 低 |
| **5. テスト環境** | TestConfigあり | TiDB用テスト設定なし | 中 |
| **6. Docker環境** | **TiDBコンテナ設定済み** | 設定微調整のみ | 低 |
| **7. 接続プール** | 基本設定あり | TiDB最適化パラメータ | 低 |
| **8. データ移行** | なし | **スクリプト未作成** | 高 |

### 2.1 詳細ギャップ分析

#### Requirement 1: データベース接続設定

**現状**: `config.py:131-139`
```python
if self.DB_DRIVER == "sqlite":
    ...
elif self.DB_DRIVER == "mysql":
    return f"mysql+pymysql://..."
raise ValueError(f"Unsupported DB_DRIVER: {self.DB_DRIVER}")
```

**ギャップ**:
- `tidb`ドライバーのサポート追加が必要
- TiDB Cloud接続用SSL/TLS設定が必要
- 接続パラメータ（`charset`, `ssl_ca`等）の追加

**複雑度**: 低 - 既存パターンの拡張のみ

#### Requirement 2: SQLite固有コードの互換性

**現状**: `app/models/__init__.py:13-19`
```python
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, _connection_record) -> None:
    if isinstance(dbapi_connection, SQLiteConnection):
        cursor.execute("PRAGMA foreign_keys = ON")
```

**ギャップ**:
- 既に条件分岐あり（`isinstance`チェック）
- 追加のSQLite固有ロジックが`payment_history_repository.py:102-116`に存在

**複雑度**: 低 - ほぼ対応済み

#### Requirement 3: データ型とスキーマ互換性

**現状**: SQLAlchemyモデル使用
- `ExchangeRate`: 複合主キー（from_currency, to_currency, date）
- `REAL`型: SQLiteとMySQL/TiDB両対応
- 外部キー制約: `ON DELETE CASCADE`, `ON DELETE SET NULL`

**ギャップ**:
- 複合主キーのTiDBでの動作確認（Research Needed）
- `DateTime`の`server_default=sa.text('(CURRENT_TIMESTAMP)')`のTiDB互換性確認

**複雑度**: 中 - 検証が必要

#### Requirement 4: マイグレーション管理

**現状**: `migrations/env.py`
- 環境変数からURL取得済み
- SQLAlchemyメタデータ使用

**ギャップ**:
- 既存マイグレーションファイルのTiDB互換性確認
- `op.f()`関数のインデックス名生成がTiDBで動作するか確認（Research Needed）

**複雑度**: 低 - ほぼ対応済み

#### Requirement 5: テスト環境対応

**現状**: `TestConfig`はインメモリSQLite固定
```python
DB_DRIVER: str = "sqlite"
DB_NAME: str = ":memory:"
```

**ギャップ**:
- 統合テスト用TiDB接続オプションが必要
- テスト間のデータ分離メカニズムの調整

**複雑度**: 中 - テストインフラの拡張

#### Requirement 6: Docker環境設定

**現状**: `compose.yml`
```yaml
tidb:
  image: pingcap/tidb:latest
  ports:
    - "4000:4000"
  healthcheck:
    test: ["CMD", "wget", "-qO-", "http://127.0.0.1:10080/status"]
```

**ギャップ**: なし - 既に設定済み

**複雑度**: 低

#### Requirement 7: 接続プール設定

**現状**: `config.py:146-150`
```python
"SQLALCHEMY_ENGINE_OPTIONS": {
    "pool_size": 5,
    "pool_recycle": 3600,
    "pool_pre_ping": True,
}
```

**ギャップ**:
- TiDB用の最適なプール設定値の調整
- 本番環境での接続タイムアウト設定

**複雑度**: 低

#### Requirement 8: 既存データ移行

**現状**: 移行スクリプトなし

**ギャップ**:
- SQLite→TiDBのデータ移行スクリプト作成が必要
- データ整合性検証機能が必要

**複雑度**: 高 - 新規開発

## 3. 実装アプローチ選択肢

### Option A: 既存コンポーネント拡張

**対象ファイル**:
- `app/config.py`: TiDB接続設定追加
- `app/models/__init__.py`: 条件分岐の強化
- `tests/conftest.py`: TiDBテスト設定追加

**メリット**:
- ✅ 既存パターンとの一貫性
- ✅ 変更範囲が最小
- ✅ 学習コストが低い

**デメリット**:
- ❌ `config.py`が肥大化する可能性
- ❌ SQLite/MySQL/TiDBの条件分岐が増加

### Option B: 新規コンポーネント作成

**新規ファイル**:
- `app/db/tidb_config.py`: TiDB固有設定
- `scripts/migrate_sqlite_to_tidb.py`: データ移行スクリプト

**メリット**:
- ✅ 明確な関心の分離
- ✅ テストが容易
- ✅ 将来的な拡張性

**デメリット**:
- ❌ 新規ファイルの追加
- ❌ インターフェース設計が必要

### Option C: ハイブリッドアプローチ (推奨)

**組み合わせ戦略**:
1. **既存拡張**: `config.py`にTiDB設定追加
2. **新規作成**: データ移行スクリプト
3. **新規作成**: データベースユーティリティ関数（ドライバー判定等）

**フェーズ**:
- Phase 1: 最小限の変更でTiDB接続を実現
- Phase 2: データ移行ツールの開発
- Phase 3: 本番環境への展開と最適化

**メリット**:
- ✅ バランスの取れたアプローチ
- ✅ 段階的な実装が可能
- ✅ リスクが分散

## 4. ドキュメントと実装の不整合（要対応）

テーブル定義書（`docs/db/table-definition.md`）を正とする場合、以下の不整合を解消する必要がある。

### 4.1 実装→ドキュメントへの整合化項目

| テーブル | 項目 | 現状（実装） | ドキュメント（正） | 対応内容 |
|---------|------|-------------|-------------------|---------|
| **EXCHANGE_RATES** | 主キー | 複合主キー（from_currency, to_currency, date） | `rate_id`（AUTO_INCREMENT） | モデル・マイグレーション修正 |
| **PAYMENT_HISTORY** | 追加カラム | `exchange_rate`, `converted_amount`, `subscription_name`あり | なし | カラム削除またはドキュメント追記検討 |
| **PAYMENT_HISTORY** | subscription_id | nullable=True | NOT NULL | NULL許容の正当性確認 |
| **SUBSCRIPTIONS** | next_payment_date | nullable=True | NOT NULL | NULL許容の正当性確認 |

### 4.2 未実装テーブル（要実装）

| テーブル | ドキュメント | 実装 | 対応 |
|---------|------------|------|-----|
| **NOTIFICATIONS** | 定義あり | なし | モデル・マイグレーション作成 |
| **CURRENCY_SETTINGS** | 定義あり | なし（User.base_currencyに統合） | モデル作成 + User.base_currency移行 |

### 4.3 TiDB移行への影響

- **EXCHANGE_RATES主キー変更**: 複合主キーからAUTO_INCREMENTへの変更は、データ移行時にID再割り当てが必要
- **NOTIFICATIONS/CURRENCY_SETTINGS実装**: 移行後に新規テーブル作成で対応可能
- **PAYMENT_HISTORY追加カラム**: ドキュメントに合わせて削除する場合、データ損失のリスク

### 4.4 推奨アプローチ

1. **移行スコープ**: 現在の実装ベースでTiDB移行を完了
2. **移行後タスク**: ドキュメント整合化作業を別タスクとして実施
3. **または**: 移行前に実装をドキュメントに合わせて修正

---

## 5. Research Needed

| 項目 | 優先度 | 設計フェーズでの対応 |
|-----|-------|-------------------|
| 複合主キーのTiDB互換性 | 高 | ExchangeRateモデルの検証（ドキュメント整合化で解消予定） |
| CURRENT_TIMESTAMPのTiDB動作 | 中 | マイグレーションファイルの調整 |
| TiDB Cloud SSL接続パラメータ | 高 | 本番環境設定 |
| インデックス名制限（TiDB） | 低 | マイグレーション確認 |
| NOTIFICATIONS/CURRENCY_SETTINGS実装 | 中 | 移行後の別タスク検討 |

## 6. 見積もり

| 項目 | 見積もり |
|-----|---------|
| **工数** | M (3-7日) |
| **理由** | Docker/TiDB設定は既に完了、設定変更と移行スクリプト開発が中心 |
| **リスク** | Medium |
| **理由** | 新しいDB技術だが、SQLAlchemyによる抽象化で影響範囲は限定 |

## 7. 推奨事項

1. **アプローチ**: Option C（ハイブリッド）を採用
2. **優先順位**:
   - Step 1: `config.py`にTiDB接続設定を追加
   - Step 2: SQLite固有コードの条件分岐強化
   - Step 3: テスト環境のTiDB対応
   - Step 4: データ移行スクリプト開発（現行実装ベース）
3. **移行後タスク**（別仕様として検討）:
   - EXCHANGE_RATES: 主キー構造のドキュメント整合化
   - NOTIFICATIONS/CURRENCY_SETTINGS: 未実装テーブルの作成
   - PAYMENT_HISTORY: 追加カラムの削除またはドキュメント追記
4. **設計フェーズへの引き継ぎ**: SSL設定、移行スクリプト設計、ドキュメント整合化計画

