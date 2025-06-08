"""
カスタム例外定義モジュール

このモジュールでは、アプリケーション固有のカスタム例外クラスを定義します。
これにより、エラーハンドリングがより明確になり、ドメイン固有のエラー状態を
表現できるようになります。
"""


class SubscriptionError(Exception):
    """サブスクリプション関連操作の基底例外クラス。"""

    pass


class SubscriptionNotFoundError(SubscriptionError):
    """指定されたサブスクリプションが見つからない場合に発生する例外。"""

    pass


class DuplicateSubscriptionError(SubscriptionError):
    """重複したサブスクリプションを作成しようとした場合に発生する例外。"""

    pass


class ValidationError(SubscriptionError):
    """一般的なバリデーションエラーが発生した場合の例外。"""

    pass


class LabelError(Exception):
    """ラベル関連操作の基底例外クラス。"""

    pass


class LabelNotFoundError(LabelError):
    """指定されたラベルが見つからない場合に発生する例外。"""

    pass


class DuplicateLabelError(LabelError):
    """重複したラベルを作成しようとした場合に発生する例外。"""

    pass


class LabelHierarchyError(LabelError):
    """循環参照や深さ制限など、階層構造に関するエラーの例外。"""

    pass
