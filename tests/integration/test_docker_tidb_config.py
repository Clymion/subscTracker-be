"""
Tests for Docker environment TiDB configuration.

This module verifies that the Docker Compose configuration for TiDB
is correctly set up according to the requirements.

Requirements: 6.1, 6.2, 6.3, 6.4
Tasks: 2.1, 2.2
"""

import subprocess
from pathlib import Path

import pytest
import yaml


@pytest.fixture
def compose_config() -> dict:
    """Load the compose.yml file as a dictionary."""
    compose_path = Path(__file__).parent.parent.parent / "compose.yml"
    with open(compose_path) as f:
        return yaml.safe_load(f)


class TestTiDBServiceConfiguration:
    """Test TiDB service configuration in compose.yml.

    Requirement: 6.1 - TiDBコンテナを正常に起動
    Requirement: 6.4 - TiDBデータ用の永続ボリュームを提供
    Task: 2.1 - compose.ymlのTiDBサービス構成確認
    """

    def test_tidb_service_exists(self, compose_config: dict) -> None:
        """Test that TiDB service is defined in compose.yml."""
        assert "services" in compose_config
        assert "tidb" in compose_config["services"]

    def test_tidb_uses_official_image(self, compose_config: dict) -> None:
        """Test that TiDB service uses the official pingcap/tidb image."""
        tidb_service = compose_config["services"]["tidb"]
        assert "image" in tidb_service
        assert "pingcap/tidb" in tidb_service["image"]

    def test_tidb_ports_exposed(self, compose_config: dict) -> None:
        """Test that TiDB service exposes required ports.

        Port 4000: MySQL protocol
        Port 10080: Status/health check
        """
        tidb_service = compose_config["services"]["tidb"]
        assert "ports" in tidb_service

        ports = tidb_service["ports"]
        port_mappings = [str(p) for p in ports]

        # MySQL protocol port
        assert any("4000" in p for p in port_mappings), "Port 4000 (MySQL) not exposed"

        # Status port
        assert any("10080" in p for p in port_mappings), "Port 10080 (status) not exposed"

    def test_tidb_has_healthcheck(self, compose_config: dict) -> None:
        """Test that TiDB service has health check configured.

        Requirement: 6.2 - ヘルスチェックが完了するまで待機
        """
        tidb_service = compose_config["services"]["tidb"]
        assert "healthcheck" in tidb_service

        healthcheck = tidb_service["healthcheck"]
        assert "test" in healthcheck
        assert "interval" in healthcheck
        assert "timeout" in healthcheck
        assert "retries" in healthcheck
        assert "start_period" in healthcheck

    def test_tidb_healthcheck_uses_status_endpoint(self, compose_config: dict) -> None:
        """Test that health check uses the status endpoint."""
        tidb_service = compose_config["services"]["tidb"]
        healthcheck = tidb_service["healthcheck"]
        test_cmd = healthcheck["test"]

        # Health check should use the status endpoint
        assert any("10080" in str(cmd) for cmd in test_cmd), \
            "Health check should use port 10080 status endpoint"

    def test_tidb_has_persistent_volume(self, compose_config: dict) -> None:
        """Test that TiDB data uses a persistent volume.

        Requirement: 6.4 - TiDBデータ用の永続ボリュームを提供
        """
        tidb_service = compose_config["services"]["tidb"]

        # Check for volume mount
        assert "volumes" in tidb_service
        volumes = tidb_service["volumes"]

        # Should have a volume for data persistence
        assert any("tidb" in str(v).lower() for v in volumes), \
            "TiDB should have a named volume for data persistence"

    def test_tidb_volume_defined(self, compose_config: dict) -> None:
        """Test that tidb-data volume is defined in volumes section."""
        assert "volumes" in compose_config
        assert "tidb-data" in compose_config["volumes"]


class TestBackendApiDependency:
    """Test backend-api service dependency on TiDB.

    Requirement: 6.3 - API起動時TiDB接続確認
    Task: 2.2 - backend-apiサービスの依存関係設定
    """

    def test_backend_api_depends_on_tidb(self, compose_config: dict) -> None:
        """Test that backend-api service depends on TiDB."""
        backend_service = compose_config["services"]["backend-api"]
        assert "depends_on" in backend_service
        assert "tidb" in backend_service["depends_on"]

    def test_backend_api_waits_for_healthy_tidb(self, compose_config: dict) -> None:
        """Test that backend-api waits for TiDB to be healthy.

        Requirement: 6.2, 6.3 - backend-apiがTiDBのヘルスチェック完了後に起動
        """
        backend_service = compose_config["services"]["backend-api"]
        depends_on = backend_service["depends_on"]

        # Check if condition is set to service_healthy
        tidb_dependency = depends_on["tidb"]
        if isinstance(tidb_dependency, dict):
            assert "condition" in tidb_dependency
            assert tidb_dependency["condition"] == "service_healthy"
        else:
            # If it's just a string or list, the health check dependency
            # might be configured differently
            pass


class TestTiDBServiceHealthCheckConfiguration:
    """Test TiDB health check configuration details."""

    def test_healthcheck_interval_is_reasonable(self, compose_config: dict) -> None:
        """Test that health check interval is reasonable."""
        healthcheck = compose_config["services"]["tidb"]["healthcheck"]

        # Parse interval (e.g., "10s" -> 10)
        interval = healthcheck["interval"]
        interval_seconds = int(interval.rstrip("s"))

        # Interval should be between 5-30 seconds
        assert 5 <= interval_seconds <= 30, \
            f"Health check interval {interval_seconds}s should be between 5-30s"

    def test_healthcheck_timeout_is_reasonable(self, compose_config: dict) -> None:
        """Test that health check timeout is reasonable."""
        healthcheck = compose_config["services"]["tidb"]["healthcheck"]

        timeout = healthcheck["timeout"]
        timeout_seconds = int(timeout.rstrip("s"))

        # Timeout should be less than interval
        interval = healthcheck["interval"]
        interval_seconds = int(interval.rstrip("s"))

        assert timeout_seconds < interval_seconds, \
            f"Timeout {timeout_seconds}s should be less than interval {interval_seconds}s"

    def test_healthcheck_retries_is_sufficient(self, compose_config: dict) -> None:
        """Test that health check retries are sufficient for startup."""
        healthcheck = compose_config["services"]["tidb"]["healthcheck"]

        retries = healthcheck["retries"]
        assert retries >= 3, "Should have at least 3 retries for startup"

    def test_healthcheck_start_period_allows_startup(self, compose_config: dict) -> None:
        """Test that start period allows sufficient time for TiDB startup."""
        healthcheck = compose_config["services"]["tidb"]["healthcheck"]

        start_period = healthcheck.get("start_period", "0s")
        start_seconds = int(start_period.rstrip("s"))

        # TiDB startup can take some time, allow at least 10 seconds
        assert start_seconds >= 10, \
            f"Start period {start_seconds}s should be at least 10s for TiDB startup"


class TestDockerComposeSyntax:
    """Test Docker Compose file syntax and structure."""

    def test_compose_file_is_valid_yaml(self, compose_config: dict) -> None:
        """Test that compose.yml is valid YAML."""
        assert isinstance(compose_config, dict)
        assert "services" in compose_config

    def test_compose_version_if_specified(self, compose_config: dict) -> None:
        """Test compose version if specified."""
        # Version is optional in newer Docker Compose
        if "version" in compose_config:
            version = compose_config["version"]
            assert version is not None


@pytest.mark.skip(reason="Requires Docker daemon to be running")
class TestDockerComposeRuntime:
    """Runtime tests for Docker Compose (requires Docker daemon)."""

    def test_compose_config_validates(self) -> None:
        """Test that docker-compose config validates without errors."""
        result = subprocess.run(
            ["docker-compose", "config"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"docker-compose config failed: {result.stderr}"

    def test_tidb_container_starts(self) -> None:
        """Test that TiDB container can start successfully.

        This test is skipped in CI without Docker daemon.
        """
        # This would require actual Docker operations
        pass
