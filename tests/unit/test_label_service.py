"""
Unit tests for LabelService.

Tests the business logic for label management, including CRUD operations,
hierarchy validation, and business rules enforcement, following the test list from
docs/test-list/label.md.
"""

from collections.abc import Generator
from datetime import datetime
from datetime import timezone as tz
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.constants import ErrorMessages
from app.exceptions import (
    DuplicateLabelError,
    LabelHierarchyError,
    LabelNotFoundError,
    ValidationError,
)
from app.models.label import Label
from app.services.label_service import LabelService
from tests.helpers import make_and_save_user, make_label


@pytest.fixture
def mock_label_repo() -> MagicMock:
    """Fixture to create a mock LabelRepository."""
    return MagicMock()


@pytest.fixture
def label_service(
    clean_db: Generator[Session, None, None],
    mock_label_repo: MagicMock,
) -> LabelService:
    """Fixture to create a LabelService instance with a mock repository."""
    service = LabelService(session=clean_db)
    # 実際のLabelServiceではlabel_repositoryを参照しますが、
    # SubscriptionServiceを仮置きしているため、属性を動的に設定します。
    service.label_repository = mock_label_repo
    return service


@pytest.mark.unit
class TestLabelServiceCreate:
    """Test cases for the create_label method."""

    def test_create_label_with_valid_data(
        self,
        label_service: LabelService,
        mock_label_repo: MagicMock,
        clean_db: Generator[Session, None, None],
    ):
        """Test that a label is created successfully with valid data."""
        # Arrange
        user = make_and_save_user(clean_db)
        label_data = {"name": "Productivity", "color": "#4ECDC4"}
        mock_label_repo.find_by_user_and_name_and_parent.return_value = None
        mock_label_repo.save.side_effect = lambda label: label

        # Act
        new_label = label_service.create_label(user.user_id, label_data)

        # Assert
        assert new_label is not None
        assert new_label.name == "Productivity"
        assert new_label.user_id == user.user_id
        assert new_label.color == "#4ECDC4"
        mock_label_repo.find_by_user_and_name_and_parent.assert_called_once_with(
            user.user_id,
            "Productivity",
            None,
        )
        mock_label_repo.save.assert_called_once()

    def test_create_label_with_duplicate_name_raises_error(
        self,
        label_service: LabelService,
        mock_label_repo: MagicMock,
        clean_db: Generator[Session, None, None],
    ):
        """Test creating a label with a duplicate name raises DuplicateLabelError."""
        # Arrange
        user = make_and_save_user(clean_db)
        label_data = {"name": "Work"}
        mock_label_repo.find_by_user_and_name_and_parent.return_value = Label(
            name="Work",
        )

        # Act & Assert
        with pytest.raises(DuplicateLabelError, match=ErrorMessages.DUPLICATE_LABEL):
            label_service.create_label(user.user_id, label_data)
        mock_label_repo.save.assert_not_called()

    def test_create_nested_label_successfully(
        self,
        label_service: LabelService,
        mock_label_repo: MagicMock,
        clean_db: Generator[Session, None, None],
    ):
        """Test creating a nested label successfully."""
        # Arrange
        user = make_and_save_user(clean_db)
        parent_label = make_label(user_id=user.user_id, name="Parent")
        parent_label.label_id = 1
        label_data = {"name": "Child", "color": "#FFFFFF", "parent_id": 1}

        mock_label_repo.find_by_user_and_name_and_parent.return_value = None
        mock_label_repo.find_by_id.return_value = parent_label
        mock_label_repo.save.side_effect = lambda label: label

        # Act
        new_label = label_service.create_label(user.user_id, label_data)

        # Assert
        assert new_label.parent_id == 1
        mock_label_repo.find_by_id.assert_called_once_with(1)

    def test_create_label_with_too_deep_hierarchy_raises_error(
        self,
        label_service: LabelService,
        mock_label_repo: MagicMock,
        clean_db: Generator[Session, None, None],
    ):
        """Test creating a label exceeding max hierarchy depth raises error."""
        # Arrange
        user = make_and_save_user(clean_db)
        parent_label = make_label(user_id=user.user_id)
        parent_label.label_id = 1
        label_data = {"name": "Too Deep", "color": "#000000", "parent_id": 1}

        mock_label_repo.find_by_user_and_name_and_parent.return_value = None
        mock_label_repo.find_by_id.return_value = parent_label

        # Mock the parent's depth to be at the limit
        with patch(
            "app.models.label.Label.get_depth",
            return_value=5,
        ), pytest.raises(
            ValidationError,
            match=ErrorMessages.LABEL_HIERARCHY_TOO_DEEP,
        ):
            # Act & Assert
            label_service.create_label(user.user_id, label_data)


@pytest.mark.unit
class TestLabelServiceGet:
    """Test cases for getting labels."""

    def test_get_label_by_id_for_owner(
        self,
        label_service: LabelService,
        mock_label_repo: MagicMock,
        clean_db: Generator[Session, None, None],
    ):
        """Test that a user can retrieve their own label."""
        # Arrange
        user = make_and_save_user(clean_db)
        label = make_label(user_id=user.user_id)
        label.label_id = 1
        mock_label_repo.find_by_id.return_value = label

        # Act
        found_label = label_service.get_label(user.user_id, label.label_id)

        # Assert
        assert found_label is not None
        assert found_label.user_id == user.user_id
        mock_label_repo.find_by_id.assert_called_once_with(label.label_id)

    def test_get_label_raises_not_found_for_non_existent(
        self,
        label_service: LabelService,
        mock_label_repo: MagicMock,
        clean_db: Generator[Session, None, None],
    ):
        """Test that LabelNotFoundError is raised for a non-existent label."""
        # Arrange
        user = make_and_save_user(clean_db)
        non_existent_id = 999
        mock_label_repo.find_by_id.return_value = None

        # Act & Assert
        with pytest.raises(LabelNotFoundError):
            label_service.get_label(user.user_id, non_existent_id)

    def test_get_label_raises_not_found_for_other_user(
        self,
        label_service: LabelService,
        mock_label_repo: MagicMock,
        clean_db: Generator[Session, None, None],
    ):
        """Test that LabelNotFoundError is raised for another user's label."""
        # Arrange
        owner = make_and_save_user(clean_db, username="owner", email="owner@test.com")
        other_user = make_and_save_user(
            clean_db,
            username="other",
            email="other@test.com",
        )
        label = make_label(user_id=owner.user_id)
        label.label_id = 1
        mock_label_repo.find_by_id.return_value = label

        # Act & Assert
        with pytest.raises(LabelNotFoundError):
            label_service.get_label(other_user.user_id, label.label_id)

    def test_get_labels_by_user(
        self,
        label_service: LabelService,
        mock_label_repo: MagicMock,
        clean_db: Generator[Session, None, None],
    ):
        """Test retrieving all labels for a specific user."""
        # Arrange
        user = make_and_save_user(clean_db)
        labels_list = [
            make_label(user_id=user.user_id, name="Label 1"),
            make_label(user_id=user.user_id, name="Label 2"),
        ]
        mock_label_repo.find_all_by_user_id.return_value = labels_list

        # Act
        result = label_service.get_labels_by_user(user.user_id)

        # Assert
        assert len(result) == 2
        mock_label_repo.find_all_by_user_id.assert_called_once_with(user.user_id, None)


@pytest.mark.unit
class TestLabelServiceUpdate:
    """Test cases for updating labels."""

    def test_update_label_success(
        self,
        label_service: LabelService,
        mock_label_repo: MagicMock,
        clean_db: Generator[Session, None, None],
    ):
        """Test that a label is updated successfully with valid data."""
        # Arrange
        user = make_and_save_user(clean_db)
        label = make_label(user_id=user.user_id, name="Old Name", color="#000000")
        label.label_id = 1
        update_data = {"name": "New Name", "color": "#FFFFFF"}

        mock_label_repo.find_by_id.return_value = label
        mock_label_repo.find_by_user_and_name_and_parent.return_value = None
        mock_label_repo.save.side_effect = lambda _l: _l

        # Act
        updated_label = label_service.update_label(
            user.user_id,
            label.label_id,
            update_data,
        )

        # Assert
        assert updated_label.name == "New Name"
        assert updated_label.color == "#FFFFFF"
        mock_label_repo.save.assert_called_once()

    def test_update_label_to_duplicate_name_raises_error(
        self,
        label_service: LabelService,
        mock_label_repo: MagicMock,
        clean_db: Generator[Session, None, None],
    ):
        """Test updating a label to a name that already exists raises an error."""
        # Arrange
        user = make_and_save_user(clean_db)
        label_to_update = make_label(user_id=user.user_id, name="Label 1")
        label_to_update.label_id = 1
        existing_label = make_label(user_id=user.user_id, name="Label 2")
        existing_label.label_id = 2

        update_data = {"name": "Label 2"}

        mock_label_repo.find_by_id.return_value = label_to_update
        mock_label_repo.find_by_user_and_name_and_parent.return_value = existing_label

        # Act & Assert
        with pytest.raises(DuplicateLabelError):
            label_service.update_label(
                user.user_id,
                label_to_update.label_id,
                update_data,
            )

    def test_update_label_system_label_raises_error(
        self,
        label_service: LabelService,
        mock_label_repo: MagicMock,
        clean_db: Generator[Session, None, None],
    ):
        """Test that attempting to modify a system label raises an error."""
        # Arrange
        user = make_and_save_user(clean_db)
        system_label = make_label(
            user_id=user.user_id,
            name="System",
            system_label=True,
        )
        system_label.label_id = 1
        update_data = {"name": "New System Name"}
        mock_label_repo.find_by_id.return_value = system_label

        # Act & Assert
        with pytest.raises(ValidationError, match=ErrorMessages.SYSTEM_LABEL_READONLY):
            label_service.update_label(user.user_id, system_label.label_id, update_data)


@pytest.mark.unit
class TestLabelServiceDelete:
    """Test cases for deleting labels."""

    def test_delete_label_success(
        self,
        label_service: LabelService,
        mock_label_repo: MagicMock,
        clean_db: Generator[Session, None, None],
    ):
        """Test that a label is deleted successfully."""
        # Arrange
        user = make_and_save_user(clean_db)
        label = make_label(user_id=user.user_id)
        label.label_id = 1
        mock_label_repo.find_by_id.return_value = label
        # Mock can_be_deleted to return True
        with patch.object(label, "can_be_deleted", return_value=True):
            # Act
            label_service.delete_label(user.user_id, label.label_id)

            # Assert
            mock_label_repo.find_by_id.assert_called_once_with(label.label_id)
            mock_label_repo.delete.assert_called_once_with(label)

    def test_delete_system_label_raises_error(
        self,
        label_service: LabelService,
        mock_label_repo: MagicMock,
        clean_db: Generator[Session, None, None],
    ):
        """Test that deleting a system label raises an error."""
        # Arrange
        user = make_and_save_user(clean_db)
        system_label = make_label(
            user_id=user.user_id,
            name="System",
            system_label=True,
        )
        system_label.label_id = 1
        mock_label_repo.find_by_id.return_value = system_label

        # Act & Assert
        with pytest.raises(ValidationError, match=ErrorMessages.SYSTEM_LABEL_READONLY):
            label_service.delete_label(user.user_id, system_label.label_id)

    def test_delete_label_with_children_raises_error(
        self,
        label_service: LabelService,
        mock_label_repo: MagicMock,
        clean_db: Generator[Session, None, None],
    ):
        """Test that deleting a label with children raises an error."""
        # Arrange
        user = make_and_save_user(clean_db)
        parent_label = make_label(user_id=user.user_id, name="Parent")
        parent_label.label_id = 1
        mock_label_repo.find_by_id.return_value = parent_label
        # Mock that the label has children
        with patch.object(
            parent_label,
            "can_be_deleted",
            return_value=False,
        ), pytest.raises(
            ValidationError,
            match=ErrorMessages.CANNOT_DELETE_LABEL_WITH_CHILDREN,
        ):
            # Act & Assert
            label_service.delete_label(user.user_id, parent_label.label_id)


@pytest.mark.unit
class TestLabelServiceHierarchy:
    """Test cases for hierarchical label management."""

    def test_update_label_parent_successfully(
        self,
        label_service: LabelService,
        mock_label_repo: MagicMock,
        clean_db: Generator[Session, None, None],
    ):
        """Test moving a label under a new parent."""
        # Arrange
        user = make_and_save_user(clean_db)
        label_to_move = make_label(user_id=user.user_id, name="Movable")
        label_to_move.label_id = 1
        new_parent = make_label(user_id=user.user_id, name="New Parent")
        new_parent.label_id = 2

        update_data = {"parent_id": 2}

        mock_label_repo.find_by_id.side_effect = [label_to_move, new_parent]
        # is_ancestor_of のモックを追加
        label_to_move.is_ancestor_of = MagicMock(return_value=False)
        mock_label_repo.save.side_effect = lambda _l: _l

        # Act
        updated_label = label_service.update_label(
            user.user_id,
            label_to_move.label_id,
            update_data,
        )

        # Assert
        assert updated_label.parent_id == 2
        mock_label_repo.save.assert_called_once()

    def test_update_label_to_create_circular_reference_raises_error(
        self,
        label_service: LabelService,
        mock_label_repo: MagicMock,
        clean_db: Generator[Session, None, None],
    ):
        """Test moving a parent label under its own child raises an error."""
        # Arrange
        user = make_and_save_user(clean_db)
        parent = make_label(user_id=user.user_id, name="Parent")
        parent.label_id = 1
        child = make_label(user_id=user.user_id, name="Child", parent_id=1)
        child.label_id = 2

        update_data = {"parent_id": 2}  # Move parent under child

        mock_label_repo.find_by_id.side_effect = [parent, child]
        # is_ancestor_ofがTrueを返すようにモックする(循環参照をシミュレート)  # noqa: ERA001
        parent.is_ancestor_of = MagicMock(return_value=True)

        # Act & Assert
        with pytest.raises(LabelHierarchyError, match=ErrorMessages.CIRCULAR_REFERENCE):
            label_service.update_label(user.user_id, parent.label_id, update_data)

    def test_update_label_exceeding_max_depth_raises_error(
        self,
        label_service: LabelService,
        mock_label_repo: MagicMock,
        clean_db: Generator[Session, None, None],
    ):
        """Test moving a label to a parent that would exceed max depth."""
        # Arrange
        user = make_and_save_user(clean_db)
        label_to_move = make_label(user_id=user.user_id, name="Movable")
        label_to_move.label_id = 1
        deep_parent = make_label(user_id=user.user_id, name="Deep Parent")
        deep_parent.label_id = 2

        update_data = {"parent_id": 2}

        mock_label_repo.find_by_id.side_effect = [label_to_move, deep_parent]
        # 親ラベルの深さがすでに最大値-1であると仮定
        with patch.object(
            deep_parent,
            "get_depth",
            return_value=4,
        ), patch.object(
            label_to_move,
            "get_depth",
            return_value=0,
        ), pytest.raises(
            LabelHierarchyError,
            match=ErrorMessages.LABEL_HIERARCHY_TOO_DEEP,
        ):
            # Act & Assert
            # 子ラベルを移動させると深さが最大値を超える
            label_service.update_label(
                user.user_id,
                label_to_move.label_id,
                update_data,
            )


@pytest.mark.unit
class TestLabelServiceUsage:
    """Test cases for label usage management."""

    def test_get_label_includes_usage_count(
        self,
        label_service: LabelService,
        mock_label_repo: MagicMock,
        clean_db: Generator[Session, None, None],
    ):
        """Test that get_label includes the real-time usage count."""
        # Arrange
        user = make_and_save_user(clean_db)
        now = datetime.now(tz=tz.utc)
        label = make_label(
            user_id=user.user_id,
            name="Used Label",
            created_at=now,
            updated_at=now,
        )
        label.label_id = 1

        # サービスがリポジトリから(Label, usage_count)のタプルを受け取ることを想定
        mock_label_repo.find_by_id_with_usage.return_value = (label, 5)

        # Act
        # サービスはDTOまたは辞書を返すことを想定
        result = label_service.get_label_with_usage(user.user_id, label.label_id)

        # Assert
        assert result is not None
        assert result["name"] == "Used Label"
        assert result["usage_count"] == 5
        mock_label_repo.find_by_id_with_usage.assert_called_once_with(label.label_id)

    def test_get_labels_by_user_includes_usage_count(
        self,
        label_service: LabelService,
        mock_label_repo: MagicMock,
        clean_db: Generator[Session, None, None],
    ):
        """Test that get_labels_by_user includes real-time usage counts."""
        # Arrange
        user = make_and_save_user(clean_db)
        now = datetime.now(tz=tz.utc)
        label1 = make_label(
            user_id=user.user_id,
            name="Used Label",
            created_at=now,
            updated_at=now,
        )
        label2 = make_label(
            user_id=user.user_id,
            name="Unused Label",
            created_at=now,
            updated_at=now,
        )

        mock_label_repo.find_all_by_user_id_with_usage.return_value = [
            (label1, 2),
            (label2, 0),
        ]

        # Act
        results = label_service.get_labels_by_user_with_usage(user.user_id)

        # Assert
        assert len(results) == 2
        assert results[0]["name"] == "Used Label"
        assert results[0]["usage_count"] == 2
        assert results[1]["name"] == "Unused Label"
        assert results[1]["usage_count"] == 0
        mock_label_repo.find_all_by_user_id_with_usage.assert_called_once_with(
            user.user_id
        )

    def test_delete_label_updates_subscription_relationships(
        self,
        label_service: LabelService,
        mock_label_repo: MagicMock,
        clean_db: Generator[Session, None, None],
    ):
        """
        Test that deleting a label correctly updates relationships

        (handled by cascade, but service logic should trigger it).
        """
        # Arrange
        user = make_and_save_user(clean_db)
        label = make_label(user_id=user.user_id, name="To Be Deleted")
        label.label_id = 1
        # このラベルがいくつかのサブスクリプションで使われていると仮定
        label.subscriptions = [MagicMock(), MagicMock()]

        mock_label_repo.find_by_id.return_value = label
        with patch.object(label, "can_be_deleted", return_value=True):

            # Act
            label_service.delete_label(user.user_id, label.label_id)

            # Assert
            # deleteが呼び出されることで、SQLAlchemyのcascade設定が
            # subscription_labels中間テーブルから関連レコードを削除することを期待
            mock_label_repo.delete.assert_called_once_with(label)
