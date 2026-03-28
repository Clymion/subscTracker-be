"""
カスタム例外定義モジュール

このモジュールでは、アプリケーション固有のカスタム例外クラスを定義します。
これにより、エラーハンドリングがより明確になり、ドメイン固有のエラー状態を
表現できるようになります。
"""


class SubscriptionError(Exception):
    """サブスクリプション関連操作の基底例外クラス。"""



class SubscriptionNotFoundError(SubscriptionError):
    """指定されたサブスクリプションが見つからない場合に発生する例外。"""



class SubscriptionAccessDenied(SubscriptionError):
    """サブスクリプションへのアクセス権がない場合に発生する例外。"""



class DuplicateSubscriptionError(SubscriptionError):
    """重複したサブスクリプションを作成しようとした場合に発生する例外。"""



class ValidationError(SubscriptionError):
    """一般的なバリデーションエラーが発生した場合の例外。"""



class LabelError(Exception):
    """ラベル関連操作の基底例外クラス。"""



class LabelNotFoundError(LabelError):
    """指定されたラベルが見つからない場合に発生する例外。"""



class DuplicateLabelError(LabelError):
    """重複したラベルを作成しようとした場合に発生する例外。"""



class LabelHierarchyError(LabelError):
    """循環参照や深さ制限など、階層構造に関するエラーの例外。"""





class ExchangeRateNotFoundError(Exception):
    """為替レートが見つからない場合に発生する例外。"""

    def __init__(self, target_date, from_currency, to_currency):
        self.target_date = target_date
        self.from_currency = from_currency
        self.to_currency = to_currency
        super().__init__(
            f"Exchange rate not found for {from_currency}/{to_currency} on {target_date}"
        )


class ResourceNotFoundError(Exception):
    """指定されたリソースが見つからない場合に発生する汎用例外。"""


class BadRequestError(Exception):
    """リクエストが不正である場合に発生する汎用例外。"""


class ForbiddenError(Exception):
    """アクセスが禁止されているリソースにアクセスしようとした場合に発生する汎用例外。"""

