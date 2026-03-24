from typing import Any, Type

from sqlalchemy.orm import DeclarativeBase, declared_attr


class Base(DeclarativeBase):
    __name__: str

    # Generate __tablename__ automatically
    @declared_attr.directive
    def __tablename__(cls) -> str:
        return cls.__name__.lower()
