from enum import Enum


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


class SourceType(str, Enum):
    BOOK = "BOOK"
    ORAL_TRADITION = "ORAL_TRADITION"
    WEB = "WEB"
    DOCUMENT = "DOCUMENT"
