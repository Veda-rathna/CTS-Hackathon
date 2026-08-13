"""Import all SQLAlchemy models so Alembic autogenerate can discover them.

Add a new import here whenever a new model file is created.
"""
from app.models.base import Base  # noqa: F401
from app.models.article import Article  # noqa: F401
from app.models.lcd import LCD, LCDHCPCSCode, LCDIcd10Covered, LCDIcd10NonCovered  # noqa: F401
from app.models.ncd import NCD  # noqa: F401
from app.models.contractor import Contractor  # noqa: F401
from app.models.jurisdiction import Jurisdiction  # noqa: F401

__all__ = ["Base"]
