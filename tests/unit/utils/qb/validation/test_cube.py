import pytest

from csvcubed.models.cube.cube import (
    QbColumn,
    CatalogMetadata,
    Cube,
)
from csvcubed.models.cube.qb.components.attribute import NewQbAttributeLiteral
from csvcubed.models.cube.qb.components.dimension import NewQbDimension
from csvcubed.models.cube.qb.components.measure import NewQbMeasure
from csvcubed.models.cube.qb.components.observedvalue import QbObservationValue
from csvcubed.models.cube.qb.components.unit import NewQbUnit
from csvcubed.models.cube.qb.validationerrors import CsvColumnLiteralWithUriTemplate
from csvcubed.utils.qb.validation.cube import validate_qb_component_constraints


def test_new_qb_attribute_literal_string_with_template():
    qube = Cube(
        metadata=CatalogMetadata("Some Qube"),
        data=None,
        columns=[
            QbColumn("Some Dimension", NewQbDimension(label="Some Dimension")),
            QbColumn(
                "Values",
                QbObservationValue(
                    NewQbMeasure("Some Measure"),
                    NewQbUnit("Some Unit"),
                ),
            ),
            QbColumn(
                "Some Attribute",
                NewQbAttributeLiteral(data_type="date", label="Some Attribute"),
                csv_column_uri_template="https://example.org/some_attribute/{+some_attribute}",
            ),
        ],
    )

    assert len(qube.validate()) == 0
    assert isinstance(
        validate_qb_component_constraints(qube)[0], CsvColumnLiteralWithUriTemplate
    )


if __name__ == "__main__":
    pytest.main()
