"""
Label APIのエンドポイントに関する統合テスト。

TDD（テスト駆動開発）のアプローチに従い、APIの振る舞いを定義します。
docs/test-list/label.md のテストケースに基づいています。
"""

from collections.abc import Generator

import pytest
from flask.testing import FlaskClient
from sqlalchemy.orm import Session

from app.constants import ErrorMessages
from app.models.label import Label
from app.models.user import User
from tests.helpers import (
    assert_error_response,
    assert_success_response,
    create_label_hierarchy,
    make_and_save_label,
    make_and_save_user,
    make_api_headers,
)


@pytest.fixture
def authenticated_user(
    client: FlaskClient,
    clean_db: Generator[Session, None, None],
) -> dict:
    """認証済みのユーザーを作成し、APIヘッダーを返すフィクスチャ"""
    user = make_and_save_user(
        clean_db,
        username="label_user",
        email="label@example.com",
        password="password123",
    )
    headers = make_api_headers(user_id=user.user_id)
    return {"user": user, "headers": headers}


@pytest.fixture
def user_with_labels(
    clean_db: Generator[Session, None, None],
    authenticated_user: dict,
) -> dict:
    """いくつかのラベルを持つ認証済みユーザーを準備する"""
    user: User = authenticated_user["user"]

    # トップレベルのラベル
    make_and_save_label(
        clean_db,
        user_id=user.user_id,
        name="Entertainment",
        color="#FF5733",
    )
    # 階層構造を持つラベル
    create_label_hierarchy(
        clean_db,
        user.user_id,
        [("Work", "#337BFF"), ("Project A", "#33C4FF")],
    )

    # 別のユーザーのラベル(これは取得されてはいけない)  # noqa: ERA001
    other_user = make_and_save_user(
        clean_db,
        username="other_label_user",
        email="other_label@example.com",
    )
    make_and_save_label(clean_db, user_id=other_user.user_id, name="Private")

    return authenticated_user


@pytest.mark.api
class TestGetLabelsAPI:
    """GET /api/v1/labels"""

    def test_get_labels_returns_list_for_owner(
        self,
        client: FlaskClient,
        user_with_labels: dict,
    ):
        """[正常系] GET /labels: 自分のラベル一覧（階層構造含む）を正しく取得できる"""
        # Arrange
        headers = user_with_labels["headers"]

        # Act
        response = client.get("/api/v1/labels", headers=headers)

        # Assert
        data = assert_success_response(response, 200)
        labels = data["data"]["labels"]
        assert len(labels) == 3  # Entertainment, Work, Project A
        label_names = {lbl["name"] for lbl in labels}
        assert label_names == {"Entertainment", "Work", "Project A"}
        # 'usage_count' が含まれていることを確認
        assert "usage_count" in labels[0]

    def test_get_labels_unauthorized_without_token(self, client: FlaskClient):
        """[異常系] GET /labels: 認証トークンがない場合は401エラーを返す"""
        response = client.get("/api/v1/labels")
        assert_error_response(response, 401, ErrorMessages.UNAUTHORIZED)


@pytest.mark.api
class TestCreateLabelAPI:
    """POST /api/v1/labels"""

    def test_create_label_with_valid_data_returns_201(
        self,
        client: FlaskClient,
        authenticated_user: dict,
    ):
        """[正常系] POST /labels: 有効なデータでラベルを新規作成できる"""
        headers = authenticated_user["headers"]
        label_data = {"name": "Finance", "color": "#28A745"}

        response = client.post("/api/v1/labels", json=label_data, headers=headers)

        data = assert_success_response(response, 201)
        created_label = data["data"]
        assert created_label["name"] == "Finance"
        assert created_label["color"] == "#28A745"
        assert created_label["usage_count"] == 0

    def test_create_nested_label_returns_201(
        self,
        client: FlaskClient,
        user_with_labels: dict,
        clean_db: Session,
    ):
        """[正常系] POST /labels: 親を指定して階層ラベルを作成できる"""
        headers = user_with_labels["headers"]
        user: User = user_with_labels["user"]
        parent_label = (
            clean_db.query(Label).filter_by(user_id=user.user_id, name="Work").one()
        )
        nested_label_data = {
            "name": "Sub-Project",
            "color": "#FFC107",
            "parent_id": parent_label.label_id,
        }

        response = client.post(
            "/api/v1/labels",
            json=nested_label_data,
            headers=headers,
        )

        data = assert_success_response(response, 201)
        assert data["data"]["name"] == "Sub-Project"
        assert data["data"]["parent_id"] == parent_label.label_id

    def test_create_label_with_duplicate_name_returns_400(
        self,
        client: FlaskClient,
        user_with_labels: dict,
    ):
        """[異常系] POST /labels: 同じ階層に重複した名前のラベルは作成できない"""
        headers = user_with_labels["headers"]
        label_data = {"name": "Work", "color": "#000000"}  # 既存のラベル名

        response = client.post("/api/v1/labels", json=label_data, headers=headers)

        assert_error_response(response, 400, ErrorMessages.DUPLICATE_LABEL)

    def test_get_labels_filter_by_parent_id_returns_children_only(
        self,
        client: FlaskClient,
        clean_db: Generator[Session, None, None],
        authenticated_user: dict,
    ):
        """[正常系] GET /labels?parent_id=X: 指定した親IDの子ラベルのみを取得"""
        # Arrange
        headers = authenticated_user["headers"]
        user: User = authenticated_user["user"]

        # 階層構造を作成: Entertainment > Movies > Action  # noqa: ERA001
        entertainment = make_and_save_label(
            clean_db, user_id=user.user_id, name="Entertainment", color="#FF0000",
        )
        movies = make_and_save_label(
            clean_db,
            user_id=user.user_id,
            name="Movies",
            color="#00FF00",
            parent_id=entertainment.label_id,
        )
        _action = make_and_save_label(
            clean_db,
            user_id=user.user_id,
            name="Action",
            color="#0000FF",
            parent_id=movies.label_id,
        )
        # 他の親を持つラベル
        work = make_and_save_label(
            clean_db, user_id=user.user_id, name="Work", color="#FFFF00",
        )
        _project = make_and_save_label(
            clean_db,
            user_id=user.user_id,
            name="Project",
            color="#FF00FF",
            parent_id=work.label_id,
        )

        # Act: Entertainmentの子ラベルのみ取得  # noqa: ERA001
        response = client.get(
            f"/api/v1/labels?parent_id={entertainment.label_id}", headers=headers,
        )

        # Assert
        data = assert_success_response(response, 200)
        labels = data["data"]["labels"]
        assert len(labels) == 1  # Moviesのみ
        assert labels[0]["name"] == "Movies"
        assert labels[0]["parent_id"] == entertainment.label_id

    def test_get_labels_filter_by_parent_id_null_returns_root_labels(
        self,
        client: FlaskClient,
        clean_db: Generator[Session, None, None],
        authenticated_user: dict,
    ):
        """[正常系] GET /labels?parent_id=null: ルートレベル（親なし）のラベルのみを取得"""
        # Arrange
        headers = authenticated_user["headers"]
        user: User = authenticated_user["user"]

        # ルートラベル
        entertainment = make_and_save_label(
            clean_db, user_id=user.user_id, name="Entertainment", color="#FF0000",
        )
        _work = make_and_save_label(
            clean_db, user_id=user.user_id, name="Work", color="#00FF00",
        )
        # 子ラベル
        _movies = make_and_save_label(
            clean_db,
            user_id=user.user_id,
            name="Movies",
            color="#0000FF",
            parent_id=entertainment.label_id,
        )

        # Act: ルートレベルのラベルのみ取得  # noqa: ERA001
        response = client.get("/api/v1/labels?parent_id=null", headers=headers)

        # Assert
        data = assert_success_response(response, 200)
        labels = data["data"]["labels"]
        assert len(labels) == 2  # EntertainmentとWorkのみ
        label_names = {label["name"] for label in labels}
        assert label_names == {"Entertainment", "Work"}
        # 全て parent_id が null であることを確認
        for label in labels:
            assert label["parent_id"] is None

    def test_get_labels_filter_by_nonexistent_parent_id_returns_empty(
        self,
        client: FlaskClient,
        clean_db: Generator[Session, None, None],
        authenticated_user: dict,
    ):
        """[正常系] GET /labels?parent_id=999: 存在しない親IDでは空の配列を返す"""
        # Arrange
        headers = authenticated_user["headers"]
        user: User = authenticated_user["user"]

        # いくつかラベルを作成
        make_and_save_label(
            clean_db, user_id=user.user_id, name="Entertainment", color="#FF0000",
        )

        # Act: 存在しない親ID  # noqa: ERA001
        response = client.get("/api/v1/labels?parent_id=999", headers=headers)

        # Assert
        data = assert_success_response(response, 200)
        labels = data["data"]["labels"]
        assert len(labels) == 0

    def test_get_labels_without_parent_id_returns_all_labels(
        self,
        client: FlaskClient,
        clean_db: Generator[Session, None, None],
        authenticated_user: dict,
    ):
        """[正常系] GET /labels: parent_id指定なしでは全ラベルを取得（既存動作維持）"""
        # Arrange
        headers = authenticated_user["headers"]
        user: User = authenticated_user["user"]

        # 階層構造を作成
        entertainment = make_and_save_label(
            clean_db, user_id=user.user_id, name="Entertainment", color="#FF0000",
        )
        _movies = make_and_save_label(
            clean_db,
            user_id=user.user_id,
            name="Movies",
            color="#00FF00",
            parent_id=entertainment.label_id,
        )
        _work = make_and_save_label(
            clean_db, user_id=user.user_id, name="Work", color="#0000FF",
        )

        # Act: parent_id指定なし  # noqa: ERA001
        response = client.get("/api/v1/labels", headers=headers)

        # Assert
        data = assert_success_response(response, 200)
        labels = data["data"]["labels"]
        assert len(labels) == 3  # 全ラベル
        label_names = {label["name"] for label in labels}
        assert label_names == {"Entertainment", "Movies", "Work"}

    def test_get_labels_filter_by_invalid_parent_id_returns_400(
        self,
        client: FlaskClient,
        authenticated_user: dict,
    ):
        """[異常系] GET /labels?parent_id=invalid: 無効なparent_idでは400エラー"""
        # Arrange
        headers = authenticated_user["headers"]

        # Act: 無効なparent_id  # noqa: ERA001
        response = client.get("/api/v1/labels?parent_id=invalid", headers=headers)

        # Assert
        assert_error_response(response, 400)


@pytest.mark.api
class TestUpdateLabelAPI:
    """PUT /api/v1/labels/{id}"""

    def test_update_label_with_valid_data_returns_200(
        self,
        client: FlaskClient,
        user_with_labels: dict,
        clean_db: Session,
    ):
        """[正常系] PUT /labels/{id}: ラベルを正常に更新できる"""
        headers = user_with_labels["headers"]
        user: User = user_with_labels["user"]
        label_to_update = (
            clean_db.query(Label)
            .filter_by(user_id=user.user_id, name="Entertainment")
            .one()
        )
        update_data = {"name": "Media", "color": "#DC3545"}

        response = client.put(
            f"/api/v1/labels/{label_to_update.label_id}",
            json=update_data,
            headers=headers,
        )

        data = assert_success_response(response, 200)
        assert data["data"]["name"] == "Media"
        assert data["data"]["color"] == "#DC3545"

    def test_update_label_to_create_circular_reference_returns_400(
        self,
        client: FlaskClient,
        user_with_labels: dict,
        clean_db: Session,
    ):
        """[異常系] PUT /labels/{id}: 循環参照になる更新はできない"""
        headers = user_with_labels["headers"]
        user: User = user_with_labels["user"]
        parent_label = (
            clean_db.query(Label).filter_by(user_id=user.user_id, name="Work").one()
        )
        child_label = (
            clean_db.query(Label)
            .filter_by(user_id=user.user_id, name="Project A")
            .one()
        )
        # 親ラベル(Work)の親を、その子ラベル(Project A)にしようとする
        update_data = {"parent_id": child_label.label_id}

        response = client.put(
            f"/api/v1/labels/{parent_label.label_id}",
            json=update_data,
            headers=headers,
        )

        assert_error_response(response, 400, ErrorMessages.CIRCULAR_REFERENCE)


@pytest.mark.api
class TestDeleteLabelAPI:
    """DELETE /api/v1/labels/{id}"""

    def test_delete_label_without_children_returns_204(
        self,
        client: FlaskClient,
        user_with_labels: dict,
        clean_db: Session,
    ):
        """[正常系] DELETE /labels/{id}: 子を持たないラベルを正常に削除できる"""
        headers = user_with_labels["headers"]
        user: User = user_with_labels["user"]
        # 子を持つ 'Work' ではなく、子を持たない 'Project A' を削除対象にする
        label_to_delete = (
            clean_db.query(Label)
            .filter_by(user_id=user.user_id, name="Project A")
            .one()
        )

        response = client.delete(
            f"/api/v1/labels/{label_to_delete.label_id}",
            headers=headers,
        )
        assert response.status_code == 204

        # 削除されたか確認
        get_response = client.get(
            f"/api/v1/labels/{label_to_delete.label_id}",
            headers=headers,
        )
        assert_error_response(get_response, 404, ErrorMessages.LABEL_NOT_FOUND)

    def test_delete_label_with_children_returns_400(
        self,
        client: FlaskClient,
        user_with_labels: dict,
        clean_db: Session,
    ):
        """[異常系] DELETE /labels/{id}: 子を持つラベルは削除できない"""
        headers = user_with_labels["headers"]
        user: User = user_with_labels["user"]
        # 子('Project A')を持つ 'Work' ラベルを削除しようとする
        parent_label = (
            clean_db.query(Label).filter_by(user_id=user.user_id, name="Work").one()
        )

        response = client.delete(
            f"/api/v1/labels/{parent_label.label_id}",
            headers=headers,
        )

        assert_error_response(
            response,
            400,
            ErrorMessages.CANNOT_DELETE_LABEL_WITH_CHILDREN,
        )

    def test_delete_other_users_label_returns_404(
        self,
        client: FlaskClient,
        user_with_labels: dict,
        clean_db: Session,
    ):
        """[異常系] DELETE /labels/{id}: 他のユーザーのラベルは削除できない"""
        headers = user_with_labels["headers"]
        other_user = clean_db.query(User).filter_by(username="other_label_user").one()
        other_label_id = other_user.labels[0].label_id

        response = client.delete(f"/api/v1/labels/{other_label_id}", headers=headers)

        # アクセス権がない場合、存在しないように見せかけるのが一般的
        assert_error_response(response, 404, ErrorMessages.LABEL_NOT_FOUND)
