import datetime
import json
from typing import List, Optional

import pandas as pd
import vcr
from behave import *
from csvcubeddevtools.behaviour.file import get_context_temp_dir_path
from csvcubeddevtools.helpers.file import get_test_cases_dir
from pandas.testing import assert_frame_equal

from csvcubed.cli.build import build as cli_build
from csvcubed.models.cube.columns import CsvColumn
from tests.helpers.schema_mocking import mock_json_schemas

_test_case_dir = get_test_cases_dir()
_cube_config_test_case_dir = _test_case_dir / "readers" / "cube-config"
_cassettes_dir = _test_case_dir / "vcrpy-cassettes"


@given('The existing tidy data csv file "{data_file}"')
def step_impl(context, data_file):
    data_file = _cube_config_test_case_dir / data_file
    if not data_file.exists():
        raise Exception(f"Could not find test-case file {data_file}")
    context.data_file = data_file


@given(
    'The config json file "{config_file}" and the existing tidy data csv file '
    '"{data_file}"'
)
def step_impl(context, config_file, data_file):
    config_file = _cube_config_test_case_dir / config_file
    if not config_file.exists():
        raise Exception(f"Could not find test-case file {config_file}")

    data_file = _cube_config_test_case_dir / data_file
    if not data_file.exists():
        raise Exception(f"Could not find test-case file {data_file}")

    context.config_file = config_file
    context.data_file = data_file


@when("The cube is created")
def step_impl(context):
    config_file = context.config_file if hasattr(context, "config_file") else None
    data_file = context.data_file
    scenario_name = context.scenario.name
    cassette_file_name = (
        scenario_name.rsplit("]")[1] if "]" in scenario_name else scenario_name
    )

    mocker = mock_json_schemas()
    context.add_cleanup(lambda: mocker.stop())

    context.out_dir = get_context_temp_dir_path(context) / "out"

    with vcr.use_cassette(str(_cassettes_dir / f"{cassette_file_name}.yaml")):
        cube, errors = cli_build(
            data_file,
            config_file,
            output_directory=context.out_dir,
            validation_errors_file_name="validation_errors.json",
        )

        context.cube = cube
        context.errors = errors


@then("There are no errors")
def step_impl(context):
    assert len(context.errors) == 0


@then("The cube Metadata should match")
def step_impl(context):
    expected_meta = eval(context.text.strip().replace("\r\n", ""))
    result_dict = context.cube.metadata.as_json_dict()

    if expected_meta != result_dict:
        # Print the mis-matched values if the whole dict is not equal
        for k, v in result_dict.items():
            true_value = result_dict[k]
            if isinstance(true_value, (datetime.datetime, datetime.date)):
                true_value = true_value.isoformat()

            if expected_meta[k] != true_value:
                raise Exception(
                    f"Key: {k} - result: {result_dict[k]} does not match expected: {expected_meta[k]}"
                )
    assert expected_meta == result_dict


@then("The cube columns should match")
def step_impl(context):
    cols: List[CsvColumn] = context.cube.columns
    print("cols:", cols)
    expected_cols: List[str] = json.loads(context.text)
    for col in cols:
        assert col.csv_column_title in expected_cols


@then("The cube data should match")
def step_impl(context):
    data: Optional[pd.DataFrame] = context.cube.data
    print("data:", data)
    expected_data = pd.read_json(context.text, orient="records", dtype=False)
    assert_frame_equal(expected_data, data, check_dtype=False, check_categorical=False)
