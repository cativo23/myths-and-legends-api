from enum import Enum


class Gender(str, Enum):
    male = "Male"
    female = "Female"
    unknown = "Unknown"
