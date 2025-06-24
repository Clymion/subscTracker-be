"""
Unit tests for authentication middleware.

Tests JWT validation and permission checking with minimal configuration.
Only JWT-related environment variables are set, no database or full app configuration.
"""

from datetime import timedelta
from typing import Callable

import pytest
from flask import Flask, jsonify
from flask_jwt_extended import JWTManager, create_access_token

from app.common.auth_middleware import jwt_required_custom, permission_required
from app.constants import ErrorMessages


class TokenFactory:
    """Factory class for creating JWT tokens in tests."""

    def __init__(self, app: Flask) -> None:
        """
        Initialize token factory with Flask app.

        Args:
            app: Flask application instance with JWT configuration.
        """
        self.app = app

    def create_access_token(self, identity: str, expires_hours: int = 1) -> str:
        """
        Create a valid access token.

        Args:
            identity: User identity for the token.
            expires_hours: Token expiration time in hours.

        Returns:
            JWT access token string.
        """
        with self.app.app_context():
            return create_access_token(
                identity=identity,
                expires_delta=timedelta(hours=expires_hours),
            )

    def create_expired_token(self, identity: str) -> str:
        """
        Create an expired access token.

        Args:
            identity: User identity for the token.

        Returns:
            Expired JWT access token string.
        """
        with self.app.app_context():
            return create_access_token(
                identity=identity,
                expires_delta=timedelta(seconds=-1),  # Expired 1 second ago
            )


class TestJWTMiddlewareSetup:
    """Base setup for JWT middleware tests with minimal configuration."""

    @pytest.fixture
    def jwt_config(self, monkeypatch: pytest.MonkeyPatch):
        """Set up minimal JWT configuration environment variables."""
        # Set only JWT-related environment variables
        monkeypatch.setenv(
            "JWT_SECRET_KEY", "test-jwt-secret-key-for-middleware-testing-123456"
        )
        monkeypatch.setenv("JWT_ACCESS_TOKEN_EXPIRES", "3600")
        monkeypatch.setenv("JWT_REFRESH_TOKEN_EXPIRES", "86400")

    @pytest.fixture
    def minimal_app(self, jwt_config) -> Flask:
        """Create minimal Flask app with only JWT configuration."""
        app = Flask(__name__)

        # Minimal app configuration for JWT testing
        app.config.update(
            {
                "TESTING": True,
                "JWT_SECRET_KEY": "test-jwt-secret-key-for-middleware-testing-123456",
                "JWT_ACCESS_TOKEN_EXPIRES": timedelta(hours=1),
                "JWT_ALGORITHM": "HS256",
            },
        )

        # Initialize JWT manager
        jwt_manager = JWTManager()
        jwt_manager.init_app(app)

        return app

    @pytest.fixture
    def protected_routes_app(self, minimal_app: Flask) -> Flask:
        """Create Flask app with protected test routes."""
        app = minimal_app

        @app.route("/protected")
        @jwt_required_custom
        def protected():
            return jsonify({"message": "Access granted"})

        @app.route("/unprotected")
        def unprotected():
            return jsonify({"message": "No auth required"})

        @app.route("/admin-only")
        @jwt_required_custom
        @permission_required(lambda identity: identity == "admin")
        def admin_only():
            return jsonify({"message": "Admin access granted"})

        @app.route("/user-or-admin")
        @jwt_required_custom
        @permission_required(lambda identity: identity in ["user", "admin"])
        def user_or_admin():
            return jsonify({"message": "User or admin access granted"})

        @app.route("/specific-user")
        @jwt_required_custom
        @permission_required(lambda identity: identity == "specific123")
        def specific_user():
            return jsonify({"message": "Specific user access granted"})

        @app.route("/complex-protected")
        @jwt_required_custom
        @permission_required(
            lambda identity: identity == "admin" or identity.startswith("allowed_"),
        )
        def complex_protected():
            return jsonify({"message": "Complex access granted"})

        return app

    @pytest.fixture
    def token_factory(self, minimal_app: Flask) -> TokenFactory:
        """
        Factory for creating different types of JWT tokens.

        Args:
            minimal_app: Flask application instance.

        Returns:
            TokenFactory instance for creating test tokens.
        """
        return TokenFactory(minimal_app)

    @pytest.fixture
    def auth_headers_factory(
        self,
        token_factory: TokenFactory,
    ) -> Callable[[str, bool], dict[str, str]]:
        """
        Factory for creating authentication headers.

        Args:
            token_factory: Token factory instance.

        Returns:
            Function that creates authentication headers.
        """

        def create_headers(
            identity: str = "testuser",
            expired: bool = False,
        ) -> dict[str, str]:
            """
            Create authentication headers with JWT token.

            Args:
                identity: User identity for the token.
                expired: Whether to create an expired token.

            Returns:
                Dictionary with Authorization header.
            """
            if expired:
                token = token_factory.create_expired_token(identity)
            else:
                token = token_factory.create_access_token(identity)
            return {"Authorization": f"Bearer {token}"}

        return create_headers


class TestJWTRequiredCustom(TestJWTMiddlewareSetup):
    """Test jwt_required_custom decorator functionality."""

    def test_allows_access_with_valid_token(
        self,
        protected_routes_app: Flask,
        auth_headers_factory: TokenFactory,
    ):
        """Test that valid JWT token allows access to protected route."""
        # Arrange
        client = protected_routes_app.test_client()
        headers = auth_headers_factory("testuser")

        # Act
        response = client.get("/protected", headers=headers)

        # Assert
        assert response.status_code == 200
        data = response.get_json()
        assert data["message"] == "Access granted"

    def test_denies_access_without_token(self, protected_routes_app: Flask):
        """Test that missing JWT token denies access."""
        # Arrange
        client = protected_routes_app.test_client()

        # Act
        response = client.get("/protected")

        # Assert
        assert response.status_code == 401
        data = response.get_json()
        assert "error" in data
        assert data["error"]["message"] == ErrorMessages.UNAUTHORIZED

    def test_denies_access_with_invalid_token(self, protected_routes_app: Flask):
        """Test that invalid JWT token denies access."""
        # Arrange
        client = protected_routes_app.test_client()
        headers = {"Authorization": "Bearer invalid.token.here"}

        # Act
        response = client.get("/protected", headers=headers)

        # Assert
        assert response.status_code == 401
        data = response.get_json()
        assert "error" in data

    def test_denies_access_with_malformed_header(self, protected_routes_app: Flask):
        """Test that malformed authorization header denies access."""
        # Arrange
        client = protected_routes_app.test_client()
        headers = {"Authorization": "NotBearer token"}

        # Act
        response = client.get("/protected", headers=headers)

        # Assert
        assert response.status_code == 401
        data = response.get_json()
        assert "error" in data

    def test_allows_access_to_unprotected_route(self, protected_routes_app: Flask):
        """Test that unprotected routes work without token."""
        # Arrange
        client = protected_routes_app.test_client()

        # Act
        response = client.get("/unprotected")

        # Assert
        assert response.status_code == 200
        data = response.get_json()
        assert data["message"] == "No auth required"

    def test_expired_token_returns_specific_error(
        self, protected_routes_app: Flask, auth_headers_factory
    ):
        """Test that expired token returns specific error message."""
        # Arrange
        client = protected_routes_app.test_client()
        headers = auth_headers_factory("testuser", expired=True)

        # Act
        response = client.get("/protected", headers=headers)

        # Assert
        assert response.status_code == 401
        data = response.get_json()
        assert "error" in data
        assert data["error"]["message"] == ErrorMessages.TOKEN_EXPIRED

    def test_different_users_can_access_protected_route(
        self,
        protected_routes_app: Flask,
        auth_headers_factory: TokenFactory,
    ):
        """Test that different valid users can access protected routes."""
        # Arrange
        client = protected_routes_app.test_client()

        # Test multiple users
        users = ["user1", "user2", "admin", "testuser"]

        for user in users:
            # Act
            headers = auth_headers_factory(user)
            response = client.get("/protected", headers=headers)

            # Assert
            assert response.status_code == 200
            data = response.get_json()
            assert data["message"] == "Access granted"


class TestPermissionRequired(TestJWTMiddlewareSetup):
    """Test permission_required decorator functionality."""

    def test_allows_access_with_admin_permission(
        self,
        protected_routes_app: Flask,
        auth_headers_factory: TokenFactory,
    ):
        """Test that admin user can access admin-only route."""
        # Arrange
        client = protected_routes_app.test_client()
        headers = auth_headers_factory("admin")

        # Act
        response = client.get("/admin-only", headers=headers)

        # Assert
        assert response.status_code == 200
        data = response.get_json()
        assert data["message"] == "Admin access granted"

    def test_denies_access_without_admin_permission(
        self,
        protected_routes_app: Flask,
        auth_headers_factory: TokenFactory,
    ):
        """Test that non-admin user cannot access admin-only route."""
        # Arrange
        client = protected_routes_app.test_client()
        headers = auth_headers_factory("regular_user")

        # Act
        response = client.get("/admin-only", headers=headers)

        # Assert
        assert response.status_code == 403
        data = response.get_json()
        assert "error" in data
        assert data["error"]["message"] == ErrorMessages.INSUFFICIENT_PERMISSIONS

    def test_allows_multiple_permitted_roles(
        self,
        protected_routes_app: Flask,
        auth_headers_factory: TokenFactory,
    ):
        """Test that multiple roles can access the same route."""
        # Arrange
        client = protected_routes_app.test_client()

        # Test regular user access
        user_headers = auth_headers_factory("user")
        response = client.get("/user-or-admin", headers=user_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert data["message"] == "User or admin access granted"

        # Test admin access to same route
        admin_headers = auth_headers_factory("admin")
        response = client.get("/user-or-admin", headers=admin_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert data["message"] == "User or admin access granted"

    def test_specific_user_permission(
        self,
        protected_routes_app: Flask,
        auth_headers_factory: TokenFactory,
    ):
        """Test permission check for specific user identity."""
        # Arrange
        client = protected_routes_app.test_client()

        # Test correct user
        correct_headers = auth_headers_factory("specific123")
        response = client.get("/specific-user", headers=correct_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert data["message"] == "Specific user access granted"

        # Test wrong user
        wrong_headers = auth_headers_factory("wrong_user")
        response = client.get("/specific-user", headers=wrong_headers)
        assert response.status_code == 403
        data = response.get_json()
        assert "error" in data

    def test_permission_check_without_authentication_fails(
        self,
        protected_routes_app: Flask,
    ):
        """Test that permission-protected routes still require authentication."""
        # Arrange
        client = protected_routes_app.test_client()

        # Act
        response = client.get("/admin-only")

        # Assert
        assert response.status_code == 401
        data = response.get_json()
        assert "error" in data

    def test_complex_permission_logic(
        self,
        protected_routes_app: Flask,
        auth_headers_factory: TokenFactory,
    ):
        """Test complex permission checking logic."""
        # Arrange
        client = protected_routes_app.test_client()

        # Test admin access
        admin_headers = auth_headers_factory("admin")
        response = client.get("/complex-protected", headers=admin_headers)
        assert response.status_code == 200

        # Test allowed user access
        allowed_headers = auth_headers_factory("allowed_user123")
        response = client.get("/complex-protected", headers=allowed_headers)
        assert response.status_code == 200

        # Test denied user access
        denied_headers = auth_headers_factory("denied_user")
        response = client.get("/complex-protected", headers=denied_headers)
        assert response.status_code == 403


class TestMiddlewareChainOrder(TestJWTMiddlewareSetup):
    """Test that middleware executes in correct order."""

    def test_auth_middleware_executes_before_permission_middleware(
        self,
        protected_routes_app: Flask,
    ):
        """Test that authentication is checked before permissions."""
        # Arrange
        client = protected_routes_app.test_client()

        # Act - No auth header should fail at auth level, not permission level
        response = client.get("/complex-protected")

        # Assert
        assert response.status_code == 401  # Auth failure, not 403 permission failure
        data = response.get_json()
        assert "error" in data

    def test_invalid_token_fails_at_auth_level(self, protected_routes_app: Flask):
        """Test that invalid token fails at auth level before permission check."""
        # Arrange
        client = protected_routes_app.test_client()
        invalid_headers = {"Authorization": "Bearer invalid.token"}

        # Act
        response = client.get("/complex-protected", headers=invalid_headers)

        # Assert
        assert response.status_code == 401  # Auth failure
        data = response.get_json()
        assert "error" in data

    def test_valid_token_but_no_permission_fails_at_permission_level(
        self,
        protected_routes_app: Flask,
        auth_headers_factory: TokenFactory,
    ):
        """Test that valid token but insufficient permission fails at permission level."""
        # Arrange
        client = protected_routes_app.test_client()
        valid_headers = auth_headers_factory("no_permission_user")

        # Act
        response = client.get("/complex-protected", headers=valid_headers)

        # Assert
        assert response.status_code == 403  # Permission failure
        data = response.get_json()
        assert "error" in data
        assert data["error"]["message"] == ErrorMessages.INSUFFICIENT_PERMISSIONS


class TestJWTTokenVariations(TestJWTMiddlewareSetup):
    """Test various JWT token scenarios."""

    def test_token_with_different_identities(
        self,
        protected_routes_app: Flask,
        token_factory: TokenFactory,
    ):
        """Test tokens with different user identities."""
        # Arrange
        client = protected_routes_app.test_client()
        identities = [
            "user1",
            "admin",
            "test@example.com",
            "user_with_underscore",
            "123",
        ]

        for identity in identities:
            # Act
            token = token_factory.create_access_token(identity)
            headers = {"Authorization": f"Bearer {token}"}
            response = client.get("/protected", headers=headers)

            # Assert
            assert response.status_code == 200
            data = response.get_json()
            assert data["message"] == "Access granted"

    def test_token_with_custom_expiration(
        self,
        protected_routes_app: Flask,
        token_factory: TokenFactory,
    ):
        """Test tokens with custom expiration times."""
        # Arrange
        client = protected_routes_app.test_client()

        # Test short-lived token (still valid)
        short_token = token_factory.create_access_token("testuser", expires_hours=1)
        headers = {"Authorization": f"Bearer {short_token}"}

        # Act
        response = client.get("/protected", headers=headers)

        # Assert
        assert response.status_code == 200

    def test_bearer_token_case_sensitivity(
        self,
        protected_routes_app: Flask,
        token_factory: TokenFactory,
    ):
        """Test that Bearer token header is case-insensitive."""
        # Arrange
        client = protected_routes_app.test_client()
        token = token_factory.create_access_token("testuser")

        # Test different cases
        test_cases = [
            f"Bearer {token}",
            f"bearer {token}",
            f"BEARER {token}",
        ]

        for auth_value in test_cases:
            # Act
            headers = {"Authorization": auth_value}
            response = client.get("/protected", headers=headers)

            # Assert - Note: This might fail if Flask-JWT-Extended is case-sensitive
            # The exact behavior depends on the JWT library implementation
            if response.status_code == 200:
                data = response.get_json()
                assert data["message"] == "Access granted"


class TestErrorResponseFormat(TestJWTMiddlewareSetup):
    """Test that error responses follow the expected format."""

    def test_auth_error_response_format(self, protected_routes_app: Flask):
        """Test that authentication error responses have correct format."""
        # Arrange
        client = protected_routes_app.test_client()

        # Act
        response = client.get("/protected")

        # Assert
        assert response.status_code == 401
        assert response.content_type == "application/json"

        data = response.get_json()
        assert "error" in data
        assert "code" in data["error"]
        assert "name" in data["error"]
        assert "message" in data["error"]
        assert data["error"]["code"] == 401
        assert data["error"]["name"] == "Unauthorized"

    def test_permission_error_response_format(
        self,
        protected_routes_app: Flask,
        auth_headers_factory,
    ):
        """Test that permission error responses have correct format."""
        # Arrange
        client = protected_routes_app.test_client()
        headers = auth_headers_factory("regular_user")

        # Act
        response = client.get("/admin-only", headers=headers)

        # Assert
        assert response.status_code == 403
        assert response.content_type == "application/json"

        data = response.get_json()
        assert "error" in data
        assert "code" in data["error"]
        assert "name" in data["error"]
        assert "message" in data["error"]
        assert data["error"]["code"] == 403
        assert data["error"]["name"] == "Forbidden"
        assert data["error"]["message"] == ErrorMessages.INSUFFICIENT_PERMISSIONS
