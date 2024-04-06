from dataclasses import MISSING, asdict, dataclass, fields, is_dataclass
from datetime import datetime
from typing import Any, get_args

DATETIME_TO_STR_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"


@dataclass
class DataclassBase:
    """Base class for configuration objects"""

    @classmethod
    def from_dict(cls, data: dict[str, Any]):
        """Instantiate a class from a dictionary"""
        return _instantiate_dataclass(cls, data)

    def to_dict(self) -> dict[Any, Any]:
        """
        Convert the dataclass instance to a dictionary, handling nested dataclasses.
        """
        return asdict(self)


def _instantiate_dataclass(cls: Any, data: dict[Any, Any]):
    """Utility function that recursively instantiates dataclasses from dictionaries
    while preserving nested dataclasses types
    """
    if not is_dataclass(cls):
        return data  # Not a dataclass, return the data as-is

    init_args = {}
    for field in fields(cls):
        field_value = data.get(field.name)
        field_type = field.type

        if field.name.startswith("_"):
            continue  # Skip private fields

        if is_dataclass(field_type):
            # Recursively instantiate nested dataclasses
            init_args[field.name] = _instantiate_dataclass(field_type, field_value or {})
        # else if value is list of dataclasses
        elif (
            hasattr(field_type, "__origin__")
            and field_type.__origin__ is list
            and is_dataclass(get_args(field_type)[0])
        ):
            inferred_type = get_args(field_type)[0]
            init_args[field.name] = [
                _instantiate_dataclass(inferred_type, item) for item in field_value  # type: ignore ; Type checker doesn't recognize the fact that field_value is a list
            ]
        else:
            # Assign basic type value
            if field_value:
                # if field_type is known - cast value to that type
                if field_type:
                    if field_type is datetime:
                        init_args[field.name] = _str_to_datetime(field_value)
                    else:
                        init_args[field.name] = field_type(field_value)
                else:
                    init_args[field.name] = field_value
            elif not isinstance(field.default, type(MISSING)):
                init_args[field.name] = field.default
            elif not isinstance(field.default_factory, type(MISSING)):
                init_args[field.name] = field.default_factory()  # type: ignore ; Type checker doesn't recognize default_factory and thinks it's a method
            else:
                # Try to construct default value for the field type
                init_args[field.name] = None

    return cls(**init_args)


def _datetime_to_str(dt: datetime) -> str:
    """Converts datetime to string

    Args:
        dt (datetime.datetime): Datetime to convert

    Returns:
        str: Datetime as string
    """
    return dt.strftime(DATETIME_TO_STR_FORMAT)


def _str_to_datetime(dt: str) -> datetime:
    """Converts string to datetime

    Args:
        datetime (str): Datetime as string

    Returns:
        datetime.datetime: Datetime
    """
    return datetime.strptime(dt, DATETIME_TO_STR_FORMAT)
