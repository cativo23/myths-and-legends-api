from enum import Enum


class CharacterType(str, Enum):
    human = "Human"
    animal = "Animal"
    ghost = "Ghost"
    demon = "Demon"
    apparition = "Apparition"
    spirit = "Spirit"
