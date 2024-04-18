from enum import Enum
from typing import Any, Type

from . import strings


def to_enum[T: Enum](value: Any, enum: Type[T] | None = None, default: T | None = None) -> T:
    """Looks up an enum value by its value, then by it's name. Case insensitive.

    Args:
        value (Any): The value to look up. Can be either a string or an integer.
            If any other type is provided, value is converted to a string.
        enum (Type[T]): The enum type to resolve value from.
        default (T, optional): The default value to return if the value is not found. Defaults to None.

    Returns:
        Enum: The enum value.
    """
    # Infer type from default value if not provided.
    if not enum and not default:
        raise ValueError("Enum type must be provided if default value is not provided.")

    if not enum:
        enum = type(default)  # type: ignore - linter doesn't recognize 'default' is not None in this branch.

    if not enum:  # Again, for linter. This branch is not reachable.
        raise ValueError("Enum type must be provided.")

    try:
        return enum(value)
    except ValueError:
        # Value doesn't exists, at least not in the same case.
        enum_values = list(enum.__members__.values())
        # Find the enum value by its value (case insensitive), or by its name (case insensitive).
        for enum_value in enum_values:
            if strings.alike(str(enum_value.value), str(value)):
                return enum_value
        # Fall back to name, case-insensitive as last resort.
        for enum_value in enum_values:
            if strings.alike(enum_value.name, str(value)):
                return enum_value
        # Value doesn't exists.
        if default is not None:
            return default
        raise
