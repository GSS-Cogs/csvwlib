"""
Standardise
-----------

Utilities for standardising cubes and their corresponding data values.
"""
from typing import Optional, List, Dict
import pandas as pd
from pandas.core.arrays.categorical import Categorical


from .cube import get_all_units, get_all_measures, get_columns_of_dsd_type
from csvqb.models.cube.qb import *
from csvqb.models.cube.qb.components.unit import NewQbUnit, QbMultiUnits
from csvqb.models.cube.qb.components.measure import (
    NewQbMeasure,
    QbMultiMeasureDimension,
)


def ensure_qbcube_data_is_categorical(cube: QbCube) -> None:
    """Convert each of the appropriate columns in a QbCube's dataframe to categorical data. Does the change in-place."""
    for column in cube.columns:
        is_categorical_column = (
            isinstance(column, QbColumn)
            and isinstance(
                column.component,
                (QbDimension, QbAttribute, QbMultiMeasureDimension, QbMultiUnits),
            )
            and not isinstance(column.component, QbAttributeLiteral)
        )

        if is_categorical_column:
            column_data = cube.data[column.csv_column_title]
            if not isinstance(column_data.values, Categorical):
                cube.data[column.csv_column_title] = column_data.astype("category")


def convert_data_values_to_uri_safe_values(
    cube: QbCube, raise_missing_value_exceptions: bool = True
) -> None:
    """
    Given a :obj:`~csvqb.models.cube.qb.QbCube`, **replace** all of the text-values which should be represented by URIs
    in the CSV-W output with the appropriate URIs.

    Also converts all appropriate columns to the pandas categorical format.
    """

    # We want to ensure all appropriate data is represented as categorical before we start replacing category labels.
    ensure_qbcube_data_is_categorical(cube)

    new_units = [u for u in get_all_units(cube) if isinstance(u, NewQbUnit)]
    map_unit_label_to_uri_identifier = {
        u.label: u.uri_safe_identifier for u in new_units
    }
    multi_units_columns = get_columns_of_dsd_type(cube, QbMultiUnits)
    _overwrite_labels_for_columns(
        cube,
        multi_units_columns,
        map_unit_label_to_uri_identifier,
        raise_missing_value_exceptions,
    )

    new_measures = [m for m in get_all_measures(cube) if isinstance(m, NewQbMeasure)]
    map_measure_label_to_uri_identifier = {
        m.label: m.uri_safe_identifier for m in new_measures
    }
    multi_measure_dimension_columns = get_columns_of_dsd_type(
        cube, QbMultiMeasureDimension
    )
    _overwrite_labels_for_columns(
        cube,
        multi_measure_dimension_columns,
        map_measure_label_to_uri_identifier,
        raise_missing_value_exceptions,
    )

    for attribute_column in get_columns_of_dsd_type(cube, NewQbDimension):
        if isinstance(attribute_column.component.code_list, NewQbCodeList):
            new_code_list = attribute_column.component.code_list
            map_attr_val_labels_to_uri_identifiers = dict(
                [
                    (concept.label, concept.uri_safe_identifier)
                    for concept in new_code_list.concepts
                ]
            )

            _overwrite_labels_for_columns(
                cube,
                [attribute_column],
                map_attr_val_labels_to_uri_identifiers,
                raise_missing_value_exceptions,
            )

    for attribute_column in get_columns_of_dsd_type(cube, QbAttribute):
        attribute = attribute_column.component
        new_attribute_values: List[NewQbAttributeValue] = attribute.new_attribute_values  # type: ignore
        if (
            not isinstance(attribute, QbAttributeLiteral)
            and len(new_attribute_values) > 0
        ):
            map_attr_val_labels_to_uri_identifiers = dict(
                [
                    (new_attribute_value.label, new_attribute_value.uri_safe_identifier)
                    for new_attribute_value in new_attribute_values
                ]
            )

            _overwrite_labels_for_columns(
                cube,
                [attribute_column],
                map_attr_val_labels_to_uri_identifiers,
                raise_missing_value_exceptions,
            )


def _overwrite_labels_for_columns(
    cube: QbCube,
    affected_columns: List[QbColumn],
    map_unit_label_to_new_value: Dict[str, str],
    raise_missing_values_exceptions: bool,
) -> None:
    for column in affected_columns:
        column_data = cube.data[column.csv_column_title]
        column_values = column_data.values
        assert isinstance(column_values, Categorical)
        new_category_labels: List[str] = []
        for c in column_values.categories:
            new_category_label = map_unit_label_to_new_value.get(c)
            if new_category_label is None:
                if raise_missing_values_exceptions:
                    raise ValueError(
                        f"Unable to find new category label for term '{c}' in column '{column.csv_column_title}'."
                    )
                else:
                    # Can't raise exception here, just leave the value as-is.
                    new_category_labels.append(c)
            else:
                new_category_labels.append(new_category_label)

        column_values.categories = new_category_labels
