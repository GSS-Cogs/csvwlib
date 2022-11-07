from distutils.errors import LinkError
from distutils.util import strtobool
import os
from typing import List

from csvcubed.models.cube import (
    ObservationValuesMissing,
    QbMultiUnits,
    QbObservationValue,
    Cube,
    QbColumn,
    QbAttribute,
    ExistingQbAttribute,
    NewQbAttribute,
    QbMultiMeasureDimension,
    NoUnitsDefinedError,
    BothUnitTypesDefinedError,
    BothMeasureTypesDefinedError,
    MoreThanOneUnitsColumnError,
    MoreThanOneMeasureColumnError,
    NoMeasuresDefinedError,
    NoObservedValuesColumnDefinedError,
    MoreThanOneObservationsColumnError,
    EmptyQbMultiMeasureDimensionError,
    validationerrors,
)

from csvcubed.models.cube.qb.components import observedvalue

from csvcubed.models.cube.qb.components.measure import ExistingQbMeasure, QbMeasure
from csvcubed.models.cube.qb.components.unit import QbUnit
from csvcubed.models.cube.qb.validationerrors import (
    CsvColumnUriTemplateMissingError,
    PivotedShapeMeasureColumnsExistError,
    DuplicateMeasureError,
    AttributeNotLinkedError,
    LinkedObsColumnDoesntExistError,
    LinkedToNonObsColumnError,
    HybridShapeError,
)

from csvcubedmodels.rdf.namespaces import SDMX_Attribute
from csvcubed.models.validationerror import ValidationError
from csvcubed.utils.qb.cube import get_columns_of_dsd_type

SDMX_A_OBS_STATUS_URI: str = str(SDMX_Attribute.obsStatus)


def validate_observations(cube: Cube) -> List[ValidationError]:
    errors: List[ValidationError] = []
    observed_value_columns = get_columns_of_dsd_type(cube, QbObservationValue)
    multi_units_columns = get_columns_of_dsd_type(cube, QbMultiUnits)

    if len(multi_units_columns) > 1:
        errors.append(MoreThanOneUnitsColumnError(len(multi_units_columns)))

    num_obs_val_columns = len(observed_value_columns)
    # strtobool will work for "True" and "true" inputs. And similarly, for "False" and "false".
    is_pivoted_multi_measure = strtobool(
        os.environ.get("PIVOTED_MULTI_MEASURE", "False")
    )

    if num_obs_val_columns == 0:
        errors.append(NoObservedValuesColumnDefinedError())
    elif num_obs_val_columns > 1 and not is_pivoted_multi_measure:
        errors.append(MoreThanOneObservationsColumnError(num_obs_val_columns))
    else:
        obs_val_columns_with_measure = [
            c
            for c in observed_value_columns
            if c.structural_definition.measure is not None
        ]
        obs_val_columns_without_measure = [
            c
            for c in observed_value_columns
            if not c.structural_definition.measure is None
        ]

        if any(obs_val_columns_with_measure) and any(obs_val_columns_without_measure):
            # In this case we have some obs vals with measures and some without.
            if any(get_columns_of_dsd_type(cube, QbMeasure)):
                """
                Example of an input that might result in a user ending up here:

                Location, Average Income (meas defined), Value (no meas defined), Other Measure
                Birmingham, 22, 45.6, Average Age
                """
                # Some obs vals have measures, some don't and a measure column exists.
                # This is an erroneous hybrid state between pivoted and standard shape.
                errors.append(
                    BothMeasureTypesDefinedError(
                        f"{QbObservationValue.__name__}.measure",
                        QbMultiMeasureDimension,
                        additional_explanation="A pivoted shape cube cannot have a measure dimension.",
                    )
                )

            else:
                # There are multiple obs val columns and no measure columns, so it looks like the user is aiming for a
                # pivoted shape. We assume the user wants a pivoted shape, so let them know that they're missing measures
                # against some of their obs val columns.
                # errors.append(NoMeasuresDefinedError([col.csv_column_title for col in obs_val_columns_without_measure]))
                pass
        elif len(obs_val_columns_without_measure) > 1:
            if any(get_columns_of_dsd_type(cube, QbMultiMeasureDimension)):
                # if there_exists_a_measure_column:
                """
                Example of an input that might result in a user ending up here:

                Location, Income (no meas defined), Average Age (no meas defined), Income Measure, Average Age Measure
                Birmingham, 22, 45.6, Average Income, Average Age
                """
                # There are mutliple obs val columns defined without measures, and at least one measure column defined.
                # This is an erroneous hybrid between standard and pivoted shape.
                # todo: Need too come up with a new validation error here to communicate this to the user.
                # todo: Tell them to go look at the distinctions between the standard and pivoted shape.
                measure_columns = get_columns_of_dsd_type(cube, QbMultiMeasureDimension)

                errors.append(
                    HybridShapeError(
                        obs_val_columns_with_measure,
                        obs_val_columns_without_measure,
                        measure_columns,
                    )
                )
            else:
                # There are multiple obs val columns defined without measures, so it looks like the user is aiming for a
                # pivoted shape. We assume the user wants a pivoted shape, so let them know that they're missing measures
                # against some of their obs val columns.
                errors.append(
                    NoMeasuresDefinedError(
                        [
                            col.csv_column_title
                            for col in obs_val_columns_without_measure
                        ]
                    )
                )
        elif len(obs_val_columns_without_measure) == 1:
            obs_val_column = obs_val_columns_without_measure[0]
            errors += _validate_observation_value(obs_val_column, multi_units_columns)
            errors += _validate_standard_shape_cube(cube)
        elif any(obs_val_columns_with_measure):
            obs_col_names = []
            for col in obs_val_columns_with_measure:
                obs_col_names.append(col.csv_column_title)
                obs_val_column = col
                errors += _validate_observation_value(
                    obs_val_column, multi_units_columns
                )
            errors += _validate_pivoted_shape_cube(cube, obs_col_names)
        # But we know there is a least one obs val column defined, so no need for an else here

        errors += _validate_missing_observation_values(cube, observed_value_columns[0])

    return errors


def _validate_missing_observation_values(
    cube: Cube, observed_value_column: QbColumn[QbObservationValue]
) -> List[ValidationError]:
    """
    Check whether there are any missing observation values in this dataset. If there are, ensure they have at least one
    `sdmxa:obsStatus` set against them to explain why the value is missing.
    """

    if cube.data is None:
        return []

    potential_missing_values = cube.data[
        cube.data[observed_value_column.csv_column_title].isna()
    ]

    if potential_missing_values.size > 0:
        obs_status_columns = get_observation_status_columns(cube)
        for obs_status_column in obs_status_columns:
            potential_missing_values = potential_missing_values[
                potential_missing_values[obs_status_column.csv_column_title].isna()
            ]

        if potential_missing_values.size > 0:
            return [
                ObservationValuesMissing(
                    csv_column_title=observed_value_column.csv_column_title,
                    row_numbers=set(potential_missing_values.index),
                )
            ]

    return []


def get_observation_status_columns(cube: Cube) -> List[QbColumn[QbAttribute]]:
    """
    Returns any columns in the given cube which represent `sdmxa:obsStatus` attributes.
    """
    return [
        c
        for c in get_columns_of_dsd_type(cube, QbAttribute)
        if _attribute_represents_observation_status(c.structural_definition)
    ]


def _attribute_represents_observation_status(attribute: QbAttribute) -> bool:
    if isinstance(attribute, ExistingQbAttribute):
        # todo: There is no way currently to tell whether an existing attribute is a sub property of `sdmxa:obsStatus`
        #   once we've started to implement SPARQL querying/etc. we should check here to see if
        #   `attribute.attribute_uri` does extend `sdmxa:obsStatus`. Issue #273.
        return attribute.attribute_uri == SDMX_A_OBS_STATUS_URI
    elif isinstance(attribute, NewQbAttribute):
        return (
            attribute.parent_attribute_uri is not None
            # todo: There is no way currently to tell whether an existing attribute is a sub property of
            #  `sdmxa:obsStatus` once we've started to implement SPARQL querying/etc. we should check here to see
            #  if `attribute.parent_attribute_uri` does extend `sdmxa:obsStatus`. Issue #273.
            and attribute.parent_attribute_uri == SDMX_A_OBS_STATUS_URI
        )

    return False


# erro for test3
def _validate_observation_value(
    observation_value: QbColumn[QbObservationValue],
    multi_unit_columns: List[QbColumn[QbMultiUnits]],
) -> List[ValidationError]:
    errors: List[ValidationError] = []
    if observation_value.structural_definition.unit is None:
        # if not any(multi_unit_columns):
        if len(multi_unit_columns) == 0:
            errors.append(NoUnitsDefinedError())
    else:
        # if any(multi_unit_columns):
        if len(multi_unit_columns) > 0:
            errors.append(BothUnitTypesDefinedError())

    return errors


def _validate_standard_shape_cube(cube: Cube) -> List[ValidationError]:
    errors: List[ValidationError] = []

    multi_measure_columns: List[
        QbColumn[QbMultiMeasureDimension]
    ] = get_columns_of_dsd_type(cube, QbMultiMeasureDimension)
    # if not any(multi_measure_columns):
    if len(multi_measure_columns) == 0:
        errors.append(NoMeasuresDefinedError())
    elif len(multi_measure_columns) > 1:
        errors.append(MoreThanOneMeasureColumnError(len(multi_measure_columns)))
    else:
        measure_column: QbColumn[QbMultiMeasureDimension] = multi_measure_columns[0]
        # if not any(measure_columns.structural_definition.measures)
        if len(measure_column.structural_definition.measures) == 0:
            errors.append(EmptyQbMultiMeasureDimensionError())
        else:
            all_measures_existing = all(
                [
                    isinstance(m, ExistingQbMeasure)
                    for m in measure_column.structural_definition.measures
                ]
            )

            if all_measures_existing and measure_column.csv_column_uri_template is None:
                errors.append(
                    CsvColumnUriTemplateMissingError(
                        measure_column.csv_column_title, ExistingQbMeasure
                    )
                )

    return errors


def column_error_checker(
    column: QbColumn,
    errors: list[ValidationError],
    observed_column_title: str,
    defined_col_names: set[str],
    obs_col_names: list[str],
):

    if observed_column_title is None:
        errors.append(AttributeNotLinkedError(column.csv_column_title))
    elif observed_column_title not in defined_col_names:
        errors.append(
            LinkedObsColumnDoesntExistError(
                observed_column_title, column.csv_column_title
            )
        )
    elif observed_column_title not in obs_col_names:
        errors.append(
            LinkedToNonObsColumnError(observed_column_title, column.csv_column_title)
        )


def _validate_pivoted_shape_cube(
    cube: Cube, obs_col_names: List[str]
) -> List[ValidationError]:
    errors: List[ValidationError] = []

    multi_measure_columns = get_columns_of_dsd_type(cube, QbMultiMeasureDimension)
    # if any(multi_measure_columns):
    if len(multi_measure_columns) > 0:
        """
        In this case, the user has defined a redundant measure column.
        All obs val columns already have their own measures declared.

        Location, Average Income (meas defined), Average Age (meas defined), Measure
        Birmingham, 22, 45.6, ???
        """
        errors.append(PivotedShapeMeasureColumnsExistError())

    defined_col_names = {col.csv_column_title for col in cube.columns}

    observed_value_columns = get_columns_of_dsd_type(cube, QbObservationValue)

    elements_of_obs_colums = []
    for element in observed_value_columns:
        elements_of_obs_colums.append(element.structural_definition.measure)

    if len(set(elements_of_obs_colums)) != len(elements_of_obs_colums):
        errors.append(DuplicateMeasureError(obs_col_names))

    attribute_columns = get_columns_of_dsd_type(cube, QbAttribute)
    for attribute_col in attribute_columns:
        observed_value_col_title = (
            attribute_col.structural_definition.get_observed_value_col_title()
        )
        column_error_checker(
            attribute_col,
            errors,
            observed_value_col_title,
            defined_col_names,
            obs_col_names,
        )

    unit_columns = get_columns_of_dsd_type(cube, QbMultiUnits)
    for unit_col in unit_columns:
        observed_value_col_title = (
            unit_col.structural_definition.observed_value_col_title
        )
        column_error_checker(
            unit_col, errors, observed_value_col_title, defined_col_names, obs_col_names
        )

    return errors
