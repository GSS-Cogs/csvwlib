# this script will test the validationmodel features
import pytest
from typing import List, Dict, Callable, Any
from dataclasses import dataclass

from csvcubed.utils.validations import (
    validate_int_type,
    validate_list_of_str,
    validate_str_type,
)
from csvcubed.models.validatedmodel import ValidatedModel
from csvcubed.models.validationerror import ValidateModelProperiesError

ValidationFunction = Callable[[Any, str], List[ValidateModelProperiesError]]


@dataclass
class TestClass(ValidatedModel):
    str_test_variable: str
    int_test_variable: int
    list_test_variable: List[str]

    def _get_validations(self) -> Dict[str, ValidationFunction]:
        return {
            "str_test_variable": validate_str_type,
            "int_test_variable": validate_int_type,
            "list_test_variable": validate_list_of_str,
        }


def test_validate_int_type_incorrect():

    test_instance = TestClass("test", "test", [])

    result = test_instance.validate()

    assert len(result) == 1
    assert (
        result[0].message
        == "This variable should be a integer value, check the following variable:"
    )
    assert result[0].property_name == "int_test_variable"


def test_validate_int_type_correct():

    test_instance = TestClass("test", 5, [])

    result = test_instance.validate()

    assert len(result) == 0


def test_validate_str_type_incorrect():

    test_instance = TestClass(5, 8, [])

    result = test_instance.validate()

    assert len(result) == 1
    assert (
        result[0].message
        == "This variable should be a string value, check the following variable:"
    )
    assert result[0].property_name == "str_test_variable"


def test_validate_str_type_correct():

    test_instance = TestClass("test", 8, [])

    result = test_instance.validate()

    assert len(result) == 0


def test_validate_list_type_incorrect():

    test_instance = TestClass("test", 8, "nope")

    result = test_instance.validate()

    assert len(result) == 1
    assert (
        result[0].message
        == "This variable should be a list of string values, check the following variable:"
    )
    assert result[0].property_name == "list_test_variable"

    my_list: [int] = [5, 8, 5]

    test_instance = TestClass("test", 8, my_list)

    result = test_instance.validate()

    assert len(result) == 1
    assert (
        result[0].message
        == "This variable should be a list of string values, check the following variable:"
    )
    assert result[0].property_name == "list_test_variable"


def test_validate_list_type_correct():

    my_list: [str] = ["test", "test2"]
    test_instance = TestClass("test", 8, my_list)

    result = test_instance.validate()

    assert len(result) == 0


if __name__ == "__main__":
    pytest.main()
