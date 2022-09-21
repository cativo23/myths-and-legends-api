# Import all the models, so that Base has them before being
# imported by Alembic
from app.db.base_class import Base  # noqa
from app.api.v1.models import User  # noqa
from app.api.v1.models import Country  # noqa
from app.api.v1.models import Character  # noqa