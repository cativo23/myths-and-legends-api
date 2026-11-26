from enum import Enum

from sqlalchemy import CheckConstraint


def enum_check(column: str, enum_cls: type[Enum], name: str) -> CheckConstraint:
    """CHECK constraint restricting `column` to the values of `enum_cls`.

    Built from the enum (not hand-typed) so the DB guard cannot drift from the
    Python enum. Values are developer-defined constants, never user input.
    """
    values = ", ".join(f"'{member.value}'" for member in enum_cls)
    return CheckConstraint(f"{column} IN ({values})", name=name)


class CategoryName(str, Enum):
    MYTH = "MYTH"
    LEGEND = "LEGEND"
    TRADITION = "TRADITION"


class EntityTypeName(str, Enum):
    CHARACTER = "CHARACTER"
    PLACE = "PLACE"
    OBJECT = "OBJECT"
    GROUP = "GROUP"
    EVENT = "EVENT"


class CharacteristicType(str, Enum):
    PHYSICAL = "PHYSICAL"
    APPEARANCE = "APPEARANCE"
    ABILITY = "ABILITY"
    WEAKNESS = "WEAKNESS"


class RelationType(str, Enum):
    MOTHER_CHILD = "MOTHER_CHILD"
    FATHER_CHILD = "FATHER_CHILD"
    SIBLINGS = "SIBLINGS"
    GUARDIAN_PLACE = "GUARDIAN_PLACE"
    ENEMIES = "ENEMIES"
    ALLIES = "ALLIES"


# Stored as a forward/reverse row pair: creating or deleting one side acts on both.
SYMMETRIC_RELATION_TYPES = frozenset(
    {RelationType.SIBLINGS, RelationType.ALLIES, RelationType.ENEMIES}
)


class SourceType(str, Enum):
    BOOK = "BOOK"
    ORAL_TRADITION = "ORAL_TRADITION"
    WEB = "WEB"
    DOCUMENT = "DOCUMENT"
