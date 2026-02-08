"""Example: Using @spec with complex and custom types.

Demonstrates validation with generic collections, Optional/Union types,
and Pydantic models as type annotations.
"""

from pydantic import BaseModel

from specwright import spec


# --- Custom types ---


class Address(BaseModel):
    street: str
    city: str
    zip_code: str


class User(BaseModel):
    name: str
    age: int
    address: Address


# --- Spec-decorated functions ---


@spec
def find_adults(users: list[User]) -> list[str]:
    """Return names of users aged 18 or older."""
    return [u.name for u in users if u.age >= 18]


@spec
def merge_configs(base: dict[str, int], overrides: dict[str, int]) -> dict[str, int]:
    """Merge two config dicts, with overrides taking precedence."""
    return {**base, **overrides}


@spec
def first_or_default(items: list[str], default: str | None) -> str | None:
    """Return the first item, or the default if the list is empty."""
    return items[0] if items else default


if __name__ == "__main__":
    addr = Address(street="123 Main St", city="Springfield", zip_code="62704")
    users = [
        User(name="Alice", age=30, address=addr),
        User(name="Bob", age=15, address=addr),
        User(name="Charlie", age=22, address=addr),
    ]

    print(find_adults(users))  # ['Alice', 'Charlie']
    print(merge_configs({"a": 1, "b": 2}, {"b": 3, "c": 4}))  # {'a': 1, 'b': 3, 'c': 4}
    print(first_or_default([], None))  # None
    print(first_or_default(["x", "y"], "default"))  # x
