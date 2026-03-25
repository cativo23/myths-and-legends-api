"""Shared enums for the API"""

from enum import Enum


class CharacterType(str, Enum):
    human = "Human"
    animal = "Animal"
    ghost = "Ghost"
    demon = "Demon"
    apparition = "Apparition"
    spirit = "Spirit"


class Gender(str, Enum):
    male = "Male"
    female = "Female"
    unknown = "Unknown"
