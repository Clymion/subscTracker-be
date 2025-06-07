from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Import all models here to register them with SQLAlchemy
from app.models.association_tables import subscription_labels
from app.models.label import Label
from app.models.subscription import Subscription
from app.models.user import User

# 他のモデルも同様にインポートしていく
