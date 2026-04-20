from dataclasses import dataclass


@dataclass
class User:
    name: str
    age: int


def age_of(user):
    return user.age

