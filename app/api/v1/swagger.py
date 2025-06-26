"""
Swagger UIとOpenAPI仕様書を配信するためのモジュール
"""

from pathlib import Path
from typing import Literal

from flask import Blueprint, Response, jsonify
from flask_swagger_ui import get_swaggerui_blueprint
from prance import ResolvingParser

# --- 定数定義 ---
# Swagger UIを表示するURL
SWAGGER_URL = "/api/docs"
# OpenAPI仕様書(JSON形式)を配信するURL (= `swagger_spec`エンドポイントを指す)
API_URL = "/api/v1/swagger.json"

# --- Blueprintの作成 ---
swagger_spec_bp = Blueprint("swagger_spec", __name__)


# --- エンドポイントの定義 ---
@swagger_spec_bp.route("/swagger.json")
def swagger_spec() -> Response | tuple[Response, Literal[500]]:
    """
    分割されたopenapi.yamlファイルを解決し、単一のJSONとして配信するエンドポイント
    """
    try:
        # Dockerコンテナのワーキングディレクトリからの相対パスで仕様書ファイルを指定
        spec_path = Path.cwd() / "docs" / "openapi" / "build" / "openapi.yaml"
        # ResolvingParserがYAMLファイルを解析
        parser = ResolvingParser(str(spec_path))
        return jsonify(parser.specification)
    except Exception as e:
        return jsonify({"error": f"Swagger仕様書の読み込みに失敗しました: {e}"}), 500


# --- Swagger UI自体を表示するためのBlueprint ---
swagger_ui_bp = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={"app_name": "SubsTracker API - Swagger UI"},
)
