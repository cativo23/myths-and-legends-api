# Import all the models, so that Base has them before being
# imported by Alembic
from app.db.base_class import Base  # noqa
from app.api.v1.domains.users.models.user import User  # noqa
from app.api.v1.domains.countries.models.country import Country  # noqa
from app.api.v1.entities.models import Category  # noqa
from app.api.v1.entities.models import EntityType  # noqa
from app.api.v1.entities.models import Entity  # noqa
from app.api.v1.entities.models import Characteristic  # noqa
from app.api.v1.entities.models import Location  # noqa
from app.api.v1.entities.models import EntityRelation  # noqa
from app.api.v1.entities.models import Source  # noqa
