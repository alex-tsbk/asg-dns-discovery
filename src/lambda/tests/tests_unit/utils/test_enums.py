from enum import Enum
from multiprocessing import Value

import pytest
from app.utils.enums import to_enum


class MyEnum(Enum):
    VALUE1 = 1
    VALUE2 = 2
    VALUE3 = 3


def test_to_enum_should_convert_value_to_enum():
    result = to_enum(2, MyEnum)
    assert result == MyEnum.VALUE2


def test_to_enum_should_convert_string_value_to_enum():
    result = to_enum("VALUE3", MyEnum)
    assert result == MyEnum.VALUE3


def test_to_enum_should_convert_lowercase_string_value_to_enum():
    result = to_enum("value1", MyEnum)
    assert result == MyEnum.VALUE1


def test_to_enum_should_raise_key_error_for_invalid_value():
    with pytest.raises(ValueError):
        result = to_enum("INVALID", MyEnum)


class MyEnum2(Enum):
    VALUE1 = "one"
    VALUE2 = "value1"


def test_to_enum_should_prioritize_value_over_name():
    result = to_enum("value1", MyEnum2)
    assert result == MyEnum2.VALUE2
