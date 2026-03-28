# Research & Design Decisions

---
**Purpose**: Capture discovery findings, architectural investigations, and rationale that inform the technical design.

**Usage**:
- Log research activities and outcomes during the discovery phase.
- Document design decision trade-offs that are too detailed for `design.md`.
- Provide references and evidence for future audits or reuse.
---

## Summary
- **Feature**: migrate-sqlite-to-tidb
- **Discovery Scope**: Complex Integration
- **Key Findings**:
  - TiDB is MySQL 8.0 protocol compatible, enabling use of standard MySQL drivers (pymysql already in dependencies)
  - Existing SQLAlchemy models are already database-agnostic and should work with minimal modifications
  - The SQLite PRAGMA event listener in `app/models/__init__.py` is the primary SQLite-specific code requiring conditional execution
  - Docker Compose already includes TiDB service configuration with health checks

## Research Log

### TiDB MySQL Compatibility Analysis
- **Context**: Verify TiDB compatibility with existing SQLAlchemy models and MySQL drivers.
- **Sources Consulted**: TiDB documentation (MySQL 8.0 compatibility), SQLAlchemy MySQL dialect documentation, existing codebase analysis
- **Findings**:
  - TiDB implements MySQL 8.0 wire protocol compatibility
  - Standard MySQL drivers work: pymysql, mysql-connector-python
  - SQLAlchemy `mysql+pymysql://` dialect is fully compatible
  - Foreign keys with CASCADE/SET NULL are supported
  - Composite primary keys are supported
  - Auto-increment columns work with AUTO_INCREMENT
  - REAL type maps to DOUBLE in TiDB
  - DateTime with server_default=func.now() works correctly
- **Implications**: Migration primarily requires configuration changes, not model rewrites. SQLAlchemy abstraction layer already provides the necessary insulation.

### Existing Codebase Analysis
- **Context**: Identify SQLite-specific code and evaluate migration impact.
- **Sources Consulted**: Code review of `app/config.py`, `app/models/__init__.py`, `migrations/env.py`, `tests/conftest.py`
- **Findings**:
  - `app/config.py`: Already supports `DB_DRIVER` environment variable with "sqlite" and "mysql" options. TiDB can use "mysql" driver or add dedicated "tidb" alias.
  - `app/models/__init__.py`: Contains `set_sqlite_pragma` event listener that sets `PRAGMA foreign_keys = ON` - this is SQLite-specific and must be conditionally executed.
  - `migrations/env.py`: Already reads `DATABASE_URL` from environment or falls back to `app_config.database_url` - already database-agnostic.
  - `tests/conftest.py`: Uses in-memory SQLite for tests - need to support TiDB testing option.
  - `compose.yml`: Already has TiDB service with health check configured.
  - `pyproject.toml`: `pymysql` dependency already present.
- **Implications**: Core architecture is well-prepared for multi-database support. Primary changes needed are:
  1. Add "tidb" driver support in config
  2. Make PRAGMA listener conditional
  3. Add TiDB-specific connection pool settings
  4. Ensure test infrastructure supports TiDB

### Data Model Compatibility Review
- **Context**: Verify all existing models are TiDB-compatible.
- **Sources Consulted**: Code review of all model files in `app/models/`
- **Findings**:
  - `User`: Standard model with Integer primary key, String columns, DateTime timestamps - fully compatible.
  - `Subscription`: Uses REAL for price (maps to DOUBLE), Date/DateTime columns, multiple indexes - fully compatible.
  - `ExchangeRate`: Composite primary key (from_currency, to_currency, date) - TiDB supports this.
  - `Label`: Self-referential foreign key (parent_id), Boolean column - fully compatible.
  - `PaymentHistory`: Complex foreign key constraint to ExchangeRate composite key - TiDB supports this.
  - `subscription_labels`: Association table with composite primary key - fully compatible.
- **Implications**: All models are TiDB-compatible without modification. SQLAlchemy abstraction prevents dialect-specific issues.

### Connection Pool Considerations
- **Context**: Determine optimal connection pool settings for TiDB.
- **Sources Consulted**: SQLAlchemy documentation, TiDB best practices
- **Findings**:
  - TiDB benefits from connection pooling due to distributed nature
  - `pool_pre_ping=True` recommended for detecting stale connections
  - `pool_recycle` recommended for long-running connections (default 3600s in current config)
  - `pool_size` should be tuned based on expected load (default 5 in current config)
- **Implications**: Existing connection pool settings in `to_flask_config()` are already appropriate for TiDB.

## Architecture Pattern Evaluation

| Option | Description | Strengths | Risks / Limitations | Notes |
|--------|-------------|-----------|---------------------|-------|
| Environment Variable Driver Selection | Use `DB_DRIVER` to switch between SQLite/TiDB at runtime | Simple configuration, existing pattern, no code duplication | Requires testing both drivers | Already partially implemented |
| Dual Configuration Classes | Separate config classes for SQLite and TiDB | Clear separation of concerns | Code duplication, maintenance overhead | Not recommended - current approach is better |
| Feature Flag Migration | Gradual rollout with feature flags | Safe migration path | Complexity for simple migration | Over-engineering for this use case |

## Design Decisions

### Decision: Use "tidb" as dedicated driver name
- **Context**: Need to decide on driver identifier for TiDB connections
- **Alternatives Considered**:
  1. Reuse "mysql" driver name — simple, but loses clarity
  2. Add "tidb" as dedicated driver — explicit and self-documenting
- **Selected Approach**: Add "tidb" as a dedicated driver name that uses the MySQL protocol
- **Rationale**: "tidb" provides clear intent in configuration and logs, while internally using MySQL protocol compatibility
- **Trade-offs**: Slight code addition vs improved clarity
- **Follow-up**: Ensure documentation reflects "tidb" driver usage

### Decision: Conditional SQLite PRAGMA execution
- **Context**: SQLite-specific PRAGMA statements must not execute for TiDB connections
- **Alternatives Considered**:
  1. Remove PRAGMA entirely — breaks SQLite foreign key enforcement
  2. Move to SQLite-specific config method — scattered logic
  3. Conditional execution based on driver — clean separation
- **Selected Approach**: Modify event listener to check driver type before executing PRAGMA
- **Rationale**: Preserves SQLite functionality while enabling TiDB support
- **Trade-offs**: Slight complexity in event listener vs maintaining dual database support
- **Follow-up**: Add utility function `is_sqlite_driver()` for driver detection

### Decision: Maintain test SQLite as default for unit tests
- **Context**: Test infrastructure should support both SQLite (fast unit tests) and TiDB (integration tests)
- **Alternatives Considered**:
  1. Require TiDB for all tests — slower, more complex
  2. Split test configurations — maintain two test configurations
- **Selected Approach**: Keep SQLite as default for TestConfig, add optional TiDB test configuration
- **Rationale**: SQLite in-memory is ideal for fast unit tests; TiDB integration tests can be run separately
- **Trade-offs**: Need to maintain test compatibility with both databases
- **Follow-up**: Add CI workflow for TiDB integration tests

### Decision: Reuse existing migrations with TiDB-compatible DDL
- **Context**: Determine migration strategy for TiDB schema
- **Alternatives Considered**:
  1. Create new migration branch for TiDB — divergent history
  2. Regenerate all migrations — loses history
  3. Reuse existing migrations — SQLAlchemy dialect handles differences
- **Selected Approach**: Reuse existing Alembic migrations; SQLAlchemy generates TiDB-compatible DDL
- **Rationale**: SQLAlchemy's dialect abstraction generates appropriate DDL for MySQL/TiDB
- **Trade-offs**: May need to review migration files for any SQLite-specific syntax
- **Follow-up**: Test migration execution against TiDB

## Risks & Mitigations

- **Risk**: Existing migrations contain SQLite-specific syntax
  - **Mitigation**: Review migrations during implementation; regenerate if necessary

- **Risk**: Data migration from SQLite to TiDB may have data type mismatches
  - **Mitigation**: Use SQLAlchemy models as source of truth; export/import via model layer

- **Risk**: Test suite may have SQLite-specific test fixtures
  - **Mitigation**: Review and update test fixtures to be database-agnostic

- **Risk**: Performance differences between SQLite and TiDB
  - **Mitigation**: Implement connection pooling; benchmark critical queries

- **Risk**: Transaction behavior differences (SQLite: serializable, TiDB: snapshot isolation)
  - **Mitigation**: Review transaction boundaries; ensure consistency

## References
- TiDB Documentation: MySQL Compatibility (https://docs.pingcap.com/tidb/stable/mysql-compatibility)
- SQLAlchemy MySQL Dialect: https://docs.sqlalchemy.org/en/20/dialects/mysql.html
- PyMySQL Driver: https://pypi.org/project/PyMySQL/
- Alembic Migration Guide: https://alembic.sqlalchemy.org/en/latest/tutorial.html
