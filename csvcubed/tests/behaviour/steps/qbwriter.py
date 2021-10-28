import pandas as pd
from pathlib import Path
from behave import Given, When, Then, Step
from devtools.behave.file import get_context_temp_dir_path

from csvcubed.models.cube import *
from csvcubed.writers.qbwriter import QbWriter
from csvcubed.utils.qb.cube import validate_qb_component_constraints
from csvcubed.utils.csvw import get_first_table_schema


def get_standard_catalog_metadata_for_name(
    name: str, identifier: Optional[str] = None
) -> CatalogMetadata:
    return CatalogMetadata(
        name,
        summary="Summary",
        identifier=identifier,
        description="Description",
        creator_uri="https://www.gov.uk/government/organisations/office-for-national-statistics",
        publisher_uri="https://www.gov.uk/government/organisations/office-for-national-statistics",
        theme_uris=["http://gss-data.org.uk/def/gdp#some-test-theme"],
        keywords=["Key word one", "Key word two"],
        landing_page_uri="http://example.org/landing-page",
        license_uri="http://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/",
        public_contact_point_uri="mailto:something@example.org",
    )


_standard_data = pd.DataFrame(
    {"A": ["a", "b", "c"], "D": ["e", "f", "g"], "Value": [1, 2, 3]}
)


@Given('a single-measure QbCube named "{cube_name}"')
def step_impl(context, cube_name: str):
    context.cube = _get_single_measure_cube_with_name_and_id(cube_name, None)


@Given(
    'a QbCube named "{cube_name}" with code-list defined in an existing CSV-W "{csvw_file_path}"'
)
def step_impl(context, cube_name: str, csvw_file_path: str):
    tmp_dir = get_context_temp_dir_path(context)
    csvw_path = tmp_dir / csvw_file_path
    columns = [
        QbColumn("A", NewQbDimension.from_data("A code list", _standard_data["A"])),
        QbColumn(
            "D",
            NewQbDimension("D code list", code_list=NewQbCodeListInCsvW(csvw_path)),
        ),
        QbColumn(
            "Value",
            QbSingleMeasureObservationValue(
                NewQbMeasure("Some Measure"), NewQbUnit("Some Unit")
            ),
        ),
    ]

    csv_path, _ = get_first_table_schema(csvw_path)
    code_list_data = pd.read_csv(csvw_path.parent / csv_path)
    code_list_values = code_list_data["Notation"].sample(3)

    context.cube = Cube(
        get_standard_catalog_metadata_for_name(cube_name, None),
        pd.DataFrame({"A": ["a", "b", "c"], "D": code_list_values, "Value": [1, 2, 3]}),
        columns,
    )


@Given('a single-measure QbCube with identifier "{cube_id}" named "{cube_name}"')
def step_impl(context, cube_name: str, cube_id: str):
    context.cube = _get_single_measure_cube_with_name_and_id(cube_name, cube_id)


def _get_single_measure_cube_with_name_and_id(cube_name: str, cube_id: str) -> Cube:
    columns = [
        QbColumn("A", NewQbDimension.from_data("A code list", _standard_data["A"])),
        QbColumn("D", NewQbDimension.from_data("D code list", _standard_data["D"])),
        QbColumn(
            "Value",
            QbSingleMeasureObservationValue(
                NewQbMeasure("Some Measure"), NewQbUnit("Some Unit")
            ),
        ),
    ]

    return Cube(
        get_standard_catalog_metadata_for_name(cube_name, cube_id),
        _standard_data,
        columns,
    )


@Given('a single-measure QbCube named "{cube_name}" with existing dimensions')
def step_impl(context, cube_name: str):
    columns = [
        QbColumn(
            "A",
            ExistingQbDimension("http://example.org/some/dimension/a"),
            csv_column_uri_template="http://example.org/some/codelist/a",
        ),
        QbColumn(
            "D",
            ExistingQbDimension("http://example.org/some/dimension/d"),
            csv_column_uri_template="http://example.org/some/codelist/d",
        ),
        QbColumn(
            "Value",
            QbSingleMeasureObservationValue(
                NewQbMeasure("Some Measure"), NewQbUnit("Some Unit")
            ),
        ),
    ]

    context.cube = Cube(
        get_standard_catalog_metadata_for_name(cube_name), _standard_data, columns
    )


@Given('a single-measure QbCube named "{cube_name}" with duplicate rows')
def step_impl(context, cube_name: str):
    data = pd.DataFrame({"A": ["a", "a"], "Value": [1, 1]})
    columns = [
        QbColumn("A", NewQbDimension.from_data("A Dimension", data["A"])),
        QbColumn(
            "Value",
            QbSingleMeasureObservationValue(
                NewQbMeasure("Some Measure"), NewQbUnit("Some Unit")
            ),
        ),
    ]

    context.cube = Cube(
        get_standard_catalog_metadata_for_name(cube_name), data, columns
    )


@Given(
    'a single-measure QbCube named "{cube_name}" with codes not defined in the code-list'
)
def step_impl(context, cube_name: str):
    columns = [
        QbColumn(
            "A",
            NewQbDimension(
                "A code list",
                code_list=NewQbCodeList(
                    get_standard_catalog_metadata_for_name("A code list"),
                    [NewQbConcept("a"), NewQbConcept("b")],  # Deliberately missing "c"
                ),
            ),
        ),
        QbColumn("D", NewQbDimension.from_data("D code list", _standard_data["D"])),
        QbColumn(
            "Value",
            QbSingleMeasureObservationValue(
                NewQbMeasure("Some Measure"), NewQbUnit("Some Unit")
            ),
        ),
    ]

    context.cube = Cube(
        get_standard_catalog_metadata_for_name(cube_name), _standard_data, columns
    )


@Given(
    'a single-measure QbCube named "{cube_name}" with optional attribute values missing'
)
def step_impl(context, cube_name: str):
    data = pd.DataFrame(
        {
            "Some Dimension": ["a", "b", "c"],
            "Some Attribute": ["attr-a", float("nan"), "attr-c"],
            "Value": [1, 2, 3],
        }
    )
    columns = [
        QbColumn(
            "Some Dimension",
            NewQbDimension.from_data("Some Dimension", data["Some Dimension"]),
        ),
        QbColumn(
            "Some Attribute",
            NewQbAttribute.from_data("Some Attribute", data["Some Attribute"]),
        ),
        QbColumn(
            "Value",
            QbSingleMeasureObservationValue(
                NewQbMeasure("Some Measure"), NewQbUnit("Some Unit")
            ),
        ),
    ]

    context.cube = Cube(
        get_standard_catalog_metadata_for_name(cube_name), data, columns
    )


@Given('a multi-measure QbCube named "{cube_name}"')
def step_impl(context, cube_name: str):
    data = pd.DataFrame(
        {
            "A": ["a_height", "a_length"],
            "Measure": ["height", "length"],
            "Value": [1, 20],
        }
    )
    columns = [
        QbColumn("A", NewQbDimension.from_data("A Dimension", data["A"])),
        QbColumn(
            "Measure", QbMultiMeasureDimension.new_measures_from_data(data["Measure"])
        ),
        QbColumn(
            "Value",
            QbMultiMeasureObservationValue(unit=NewQbUnit("meters")),
        ),
    ]

    context.cube = Cube(
        get_standard_catalog_metadata_for_name(cube_name), data, columns
    )


@Given('a multi-measure QbCube named "{cube_name}" with duplicate rows')
def step_impl(context, cube_name: str):
    data = pd.DataFrame(
        {
            "A": ["a_height", "a_height", "a_length"],
            "Measure": ["height", "height", "length"],
            "Value": [1, 1, 20],
        }
    )
    columns = [
        QbColumn("A", NewQbDimension.from_data("A Dimension", data["A"])),
        QbColumn(
            "Measure", QbMultiMeasureDimension.new_measures_from_data(data["Measure"])
        ),
        QbColumn(
            "Value",
            QbMultiMeasureObservationValue(unit=NewQbUnit("meters")),
        ),
    ]

    context.cube = Cube(
        get_standard_catalog_metadata_for_name(cube_name), data, columns
    )


@Given(
    'a single-measure QbCube named "{cube_name}" with new attribute values and units'
)
def step_impl(context, cube_name: str):
    data = pd.DataFrame(
        {
            "Existing Dimension": ["a", "b", "c"],
            "New Attribute": ["pending", "final", "in-review"],
            "Value": [2, 2, 2],
        }
    )
    columns = [
        QbColumn(
            "Existing Dimension", ExistingQbDimension("http://existing-dimension")
        ),
        QbColumn(
            "New Attribute",
            NewQbAttribute.from_data("New Attribute", data["New Attribute"]),
        ),
        QbColumn(
            "Value",
            QbSingleMeasureObservationValue(
                NewQbMeasure("Some Measure"), NewQbUnit("Some Unit")
            ),
        ),
    ]

    context.cube = Cube(
        get_standard_catalog_metadata_for_name(cube_name), data, columns
    )


@Given(
    'a single-measure QbCube named "{cube_name}" with one new unit extending another new unit'
)
def step_impl(context, cube_name: str):
    columns = [
        QbColumn(
            "A",
            ExistingQbDimension("http://example.org/some/dimension/a"),
            csv_column_uri_template="http://example.org/some/codelist/a",
        ),
        QbColumn(
            "D",
            ExistingQbDimension("http://example.org/some/dimension/d"),
            csv_column_uri_template="http://example.org/some/codelist/d",
        ),
        QbColumn(
            "Value",
            QbSingleMeasureObservationValue(
                NewQbMeasure("Some Measure"),
                NewQbUnit(
                    "Some Extending Unit",
                    base_unit=NewQbUnit("Some Base Unit"),
                    base_unit_scaling_factor=1000,
                    qudt_quantity_kind_uri="http://some-quantity-kind",
                    si_base_unit_conversion_multiplier=25.123123,
                ),
            ),
        ),
    ]

    context.cube = Cube(
        get_standard_catalog_metadata_for_name(cube_name), _standard_data, columns
    )


@Then('turtle should be written to "{file}"')
def step_impl(context, file: str):
    temp_dir = get_context_temp_dir_path(context)

    with open(Path(temp_dir / file), "w") as ttl_file:
        ttl_file.write(context.turtle)


@When("the cube is serialised to CSV-W")
def step_impl(context):
    writer = QbWriter(context.cube)
    temp_dir = get_context_temp_dir_path(context)
    writer.write(temp_dir)


@When("the cube is serialised to CSV-W (suppressing missing uri value exceptions)")
def step_impl(context):
    writer = QbWriter(context.cube, raise_missing_uri_safe_value_exceptions=False)
    temp_dir = get_context_temp_dir_path(context)
    writer.write(temp_dir)


@Step("the CSVqb should pass all validations")
def step_impl(context):
    cube: Cube = context.cube
    errors = cube.validate()
    errors += validate_qb_component_constraints(context.cube)
    assert len(errors) == 0, [e.message for e in errors]


@Given(
    'a single-measure QbCube named "{cube_name}" with "{type}" "{data_type}" attribute'
)
def step_impl(context, cube_name: str, type: str, data_type: str):
    data = pd.DataFrame(
        {
            "A": ["uss-cerritos", "uss-titan"],
            "Value": [1, 1],
            "Reg": [75567, 80102],
            "Appeared": ["2020-08-06", "2020-10-08"],
            "First_Captain": ["William Riker", "Carol Freeman"],
        }
    )
    dim = QbColumn("A", NewQbDimension.from_data("A Dimension", data["A"]))
    val = QbColumn(
        "Value",
        QbSingleMeasureObservationValue(
            NewQbMeasure("Some Measure"), NewQbUnit("Some Unit")
        ),
    )
    if data_type == "int":
        if type == "new":
            att = QbColumn(
                "Reg",
                NewQbAttributeLiteral(data_type="int", label="Reg"),
            )
        else:
            att = QbColumn(
                "Reg",
                ExistingQbAttributeLiteral(
                    data_type="int", attribute_uri="http://some-uri"
                ),
            )
        sp1 = SuppressedCsvColumn("Appeared")
        sp2 = SuppressedCsvColumn("First_Captain")
        columns = [dim, val, att, sp1, sp2]
    elif data_type == "date":
        sp1 = SuppressedCsvColumn("Reg")
        if type == "new":
            att = QbColumn(
                "Appeared", NewQbAttributeLiteral(data_type="date", label="Appeared")
            )
        else:
            att = QbColumn(
                "Appeared",
                ExistingQbAttributeLiteral(
                    data_type="date", attribute_uri="http://some-uri"
                ),
            )
        sp2 = SuppressedCsvColumn("First_Captain")
        columns = [dim, val, sp1, att, sp2]
    elif data_type == "string":
        sp1 = SuppressedCsvColumn("Reg")
        sp2 = SuppressedCsvColumn("Appeared")
        if type == "new":
            att = QbColumn(
                "First_Captain",
                NewQbAttributeLiteral(data_type="string", label="First Captain"),
            )
        else:
            att = QbColumn(
                "First_Captain",
                ExistingQbAttributeLiteral(
                    data_type="string", attribute_uri="http://some-uri"
                ),
            )
        columns = [dim, val, sp1, sp2, att]

    context.cube = Cube(
        get_standard_catalog_metadata_for_name(cube_name), data, columns
    )


@Given(
    'a single-measure QbCube named "{cube_name}" with all new units/measures/dimensions/attributes/codelists'
)
def step_impl(context, cube_name: str):
    data = pd.DataFrame(
        {
            "New Dimension": ["a", "b", "c"],
            "New Attribute": ["university", "students", "masters"],
            "Observed Value": [1, 2, 3],
        }
    )

    columns = [
        QbColumn(
            "New Dimension",
            NewQbDimension(
                "a new codelist",
                code_list=NewQbCodeList(
                    get_standard_catalog_metadata_for_name("a new codelist"),
                    [NewQbConcept("a"), NewQbConcept("b"), NewQbConcept("c")],
                ),
            ),
        ),
        QbColumn(
            "New Attribute",
            NewQbAttribute.from_data("new_Qb_attribute", data["New Attribute"]),
        ),
        QbColumn(
            "Observed Value",
            QbSingleMeasureObservationValue(
                NewQbMeasure("Part-time"), NewQbUnit("Num of Students")
            ),
        ),
    ]

    cube = Cube(get_standard_catalog_metadata_for_name(cube_name), data, columns)

    errors = cube.validate()
    errors += validate_qb_component_constraints(cube)

    assert len(errors) == 0, [e.message for e in errors]

    context.cube = cube


@Given(
    'a multi-measure QbCube named "{cube_name}" with all new units/measures/dimensions/attributes/codelists'
)
def step_impl(context, cube_name: str):
    data = pd.DataFrame(
        {
            "New Dimension": ["a", "b", "c"],
            "New Attribute": ["university", "students", "masters"],
            "Observed Value": [1, 2, 3],
            "Measure": ["part-time", "full-time", "flex-time"],
        }
    )

    columns = [
        QbColumn(
            "New Dimension",
            NewQbDimension(
                "existing codelist",
                code_list=NewQbCodeList(
                    get_standard_catalog_metadata_for_name("a new codelist"),
                    [NewQbConcept("a"), NewQbConcept("b"), NewQbConcept("c")],
                ),
            ),
        ),
        QbColumn(
            "New Attribute",
            NewQbAttribute.from_data("new_Qb_attribute", data["New Attribute"]),
        ),
        QbColumn(
            "Observed Value",
            QbMultiMeasureObservationValue(unit=NewQbUnit("Num of students")),
        ),
        QbColumn(
            "Measure", QbMultiMeasureDimension.new_measures_from_data(data["Measure"])
        ),
    ]

    cube = Cube(get_standard_catalog_metadata_for_name(cube_name), data, columns)

    errors = cube.validate()
    errors += validate_qb_component_constraints(cube)

    assert len(errors) == 0, [e.message for e in errors]

    context.cube = cube


@Given(
    'a single measure QbCube named "{cube_name}" with existing units/measure/dimensions/attribute/codelists'
)
def step_impl(context, cube_name: str):
    data = pd.DataFrame(
        {
            "Existing Dimension": ["a", "b", "c"],
            "New Dimension": ["d", "e", "f"],
            "Existing Attribute": ["university", "students", "masters"],
            "Observed Value": [1, 2, 3],
        }
    )

    columns = [
        QbColumn(
            csv_column_title="Existing Dimension",
            component=ExistingQbDimension("http://existing/dimension"),
            csv_column_uri_template="http://existing/dimension/{+existing_dimension}",
        ),
        QbColumn(
            csv_column_title="New Dimension",
            component=NewQbDimension(
                label="existing codelist",
                code_list=ExistingQbCodeList(
                    concept_scheme_uri="http://existing/concept/scheme/uri"
                ),
            ),
        ),
        QbColumn(
            csv_column_title="Existing Attribute",
            component=ExistingQbAttribute("http://existing/attribute"),
            csv_column_uri_template="http://existing/attribute/{+existing_attribute}",
        ),
        QbColumn(
            csv_column_title="Observed Value",
            component=QbSingleMeasureObservationValue(
                ExistingQbMeasure("http://existing/measure"),
                ExistingQbUnit("http://exisiting/unit"),
            ),
        ),
    ]

    cube = Cube(get_standard_catalog_metadata_for_name(cube_name), data, columns)

    errors = cube.validate()
    errors += validate_qb_component_constraints(cube)

    assert len(errors) == 0, [e.message for e in errors]

    context.cube = cube


@Given(
    'a multi measure QbCube named "{cube_name}" with existing units/measure/dimensions/attribute/codelists'
)
def step_impl(context, cube_name: str):
    data = pd.DataFrame(
        {
            "Existing Dimension": ["a", "b", "c"],
            "New Dimension": ["d", "e", "f"],
            "Existing Attribute": ["university", "students", "masters"],
            "Observed Value": [1, 2, 3],
            "Units": ["gbp", "count", "count"],
            "Existing Measures": ["part-time", "full-time", "flex-time"],
        }
    )

    columns = [
        QbColumn(
            "Existing Dimension",
            ExistingQbDimension("http://existing/dimension"),
            csv_column_uri_template="http://existing/dimension/{+existing_dimension}",
        ),
        QbColumn(
            csv_column_title="New Dimension",
            component=NewQbDimension(
                label="existing codelist",
                code_list=ExistingQbCodeList(
                    concept_scheme_uri="http://existing/concept/scheme/uri"
                ),
            ),
        ),
        QbColumn(
            csv_column_title="Existing Attribute",
            component=ExistingQbAttribute("http://existing/attribute"),
            csv_column_uri_template="http://existing/attribute/{+existing_attribute}",
        ),
        QbColumn(
            "Observed Value",
            QbMultiMeasureObservationValue("number"),
        ),
        QbColumn(
            "Units",
            QbMultiUnits(
                [
                    ExistingQbUnit("http://existing/unit/gbp"),
                    ExistingQbUnit("http://existing/unit/count"),
                ]
            ),
            csv_column_uri_template="http://existing/unit/{+units}",
        ),
        QbColumn(
            "Existing Measures",
            QbMultiMeasureDimension(
                [
                    ExistingQbMeasure("http://existing/measure/part-time"),
                    ExistingQbMeasure("http://existing/measure/full-time"),
                    ExistingQbMeasure("http://existing/measure/flex-time"),
                ]
            ),
            csv_column_uri_template="http://existing/measure/{+existing_measures}",
        ),
    ]

    cube = Cube(get_standard_catalog_metadata_for_name(cube_name), data, columns)

    errors = cube.validate()
    errors += validate_qb_component_constraints(cube)

    assert len(errors) == 0, [e.message for e in errors]

    context.cube = cube


@Then("some additional turtle is appended to the resulting RDF")
def step_impl(context):
    rdf_to_add = context.text
    context.turtle += rdf_to_add
