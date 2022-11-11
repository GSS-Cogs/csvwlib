"""
CSV-qb Writer
-------------

Output writer for CSV-qb
"""
import itertools
import json
import logging
from pathlib import Path
from typing import Tuple, Dict, Any, Iterable

import pandas as pd

from csvcubed.models.cube import *
from csvcubed.utils.uri import (
    csvw_column_name_safe,
)
from csvcubed.utils.csvw import get_dependent_local_files
from csvcubed.utils.qb.cube import QbColumnarDsdType
from csvcubed.utils.qb.standardise import (
    convert_data_values_to_uri_safe_values,
    ensure_int_columns_are_ints,
)
from csvcubed.utils.file import copy_files_to_directory_with_structure
from .dsdhelper import QbDsdHelper
from .skoscodelistwriter import SkosCodeListWriter
from .urihelpers.cubenew import QbUriHelper
from .writerbase import WriterBase
from ..models.cube import (
    QbAttribute,
    ExistingQbAttribute,
    NewQbAttribute,
    QbMultiMeasureDimension,
    QbMultiUnits,
    QbAttributeLiteral,
)
from ..models.cube.qb.components.codelist import NewQbCodeListInCsvW
from ..utils.qb.validation.observations import get_observation_status_columns


_logger = logging.getLogger(__name__)

VIRT_UNIT_COLUMN_NAME = "virt_unit"


@dataclass
class QbWriter(WriterBase):
    cube: QbCube
    csv_file_name: str = field(init=False)
    raise_missing_uri_safe_value_exceptions: bool = field(default=True, repr=False)
    _uris: QbUriHelper = field(init=False)
    _dsd: QbDsdHelper = field(init=False)

    @property
    def csv_metadata_file_name(self) -> str:
        return f"{self.csv_file_name}-metadata.json"

    def __post_init__(self):
        self.csv_file_name = f"{self.cube.metadata.uri_safe_identifier}.csv"
        _logger.debug(
            "Initialising %s with CSV output set to '%s'",
            QbWriter.__name__,
            self.csv_file_name,
        )
        self._uris = QbUriHelper(self.cube)
        self._dsd = QbDsdHelper(self.cube, self._uris)

    def write(self, output_folder: Path):
        # Map all labels to their corresponding URI-safe-values, where possible.
        # Also converts all appropriate columns to the pandas categorical format.
        _logger.debug("Beginning CSV-W Generation: '%s'", self.csv_file_name)

        ensure_int_columns_are_ints(self.cube)

        # Bring the pandas representation of booleans inline with what the csvw spec requires
        # True != true, False != false
        if isinstance(self.cube.data, pd.DataFrame):
            for pandas_column_label in self.cube.data.columns.values:
                if self.cube.data[pandas_column_label].dtype == "bool":
                    self.cube.data[pandas_column_label] = self.cube.data[
                        pandas_column_label
                    ].apply(
                        lambda x: "true" if x is True else "false" if x is False else x
                    )

        _logger.debug("Calling data values to uri safe values")
        convert_data_values_to_uri_safe_values(
            self.cube, self.raise_missing_uri_safe_value_exceptions
        )

        tables = [
            {
                "url": self.csv_file_name,
                "tableSchema": {
                    "columns": self._generate_csvw_columns_for_cube(),
                    "foreignKeys": self._generate_foreign_keys_for_cube(),
                    "primaryKey": self._get_primary_key_columns(),
                    "aboutUrl": self._uris.get_about_url(),
                },
            }
        ]

        tables += self._get_table_references_needed_for_foreign_keys()

        self._output_new_code_list_csvws(output_folder)

        csvw_metadata = {
            "@context": "http://www.w3.org/ns/csvw",
            "@id": self._uris.get_dataset_uri(),
            "tables": tables,
            "rdfs:seeAlso": self._dsd.generate_data_structure_definitions(),
        }

        metadata_json_output_path = output_folder / self.csv_metadata_file_name
        with open(metadata_json_output_path, "w+") as f:
            _logger.debug("Writing CSV-W JSON-LD to %s", metadata_json_output_path)
            json.dump(csvw_metadata, f, indent=4)

        if self.cube.data is not None:
            csv_output_file_path = output_folder / self.csv_file_name
            _logger.debug("Writing CSV to %s", csv_output_file_path)
            self.cube.data.to_csv(csv_output_file_path, index=False)

    def _output_new_code_list_csvws(self, output_folder: Path) -> None:
        for column in self.cube.get_columns_of_dsd_type(NewQbDimension):
            code_list = column.structural_definition.code_list
            if isinstance(code_list, NewQbCodeList):
                _logger.debug(
                    "Writing code list %s to '%s' directory.", code_list, output_folder
                )

                code_list_writer = self._get_writer_for_code_list(code_list)
                code_list_writer.write(output_folder)
            elif isinstance(code_list, NewQbCodeListInCsvW):
                # find the CSV-W codelist and all dependent relative files and copy them into the output_folder
                _logger.debug(
                    "Copying legacy code list %s (with dependent files) to '%s' directory.",
                    code_list,
                    output_folder,
                )

                dependent_files = get_dependent_local_files(
                    code_list.schema_metadata_file_path
                )
                files_relative_to = code_list.schema_metadata_file_path.parent
                copy_files_to_directory_with_structure(
                    [code_list.schema_metadata_file_path] + list(dependent_files),
                    files_relative_to,
                    output_folder,
                )

    def _generate_csvw_columns_for_cube(self) -> List[Dict[str, Any]]:
        columns = [self._generate_csvqb_column(c) for c in self.cube.columns]
        if self.cube.is_pivoted_shape:
            _logger.debug("The cube is in pivoted shape")
            columns += (
                self._generate_virtual_columns_for_obs_vals_in_pivoted_shape_cube()
            )
        else:
            _logger.debug("The cube is in standard shape")
            columns += self._generate_virtual_columns_for_standard_shape_cube()
        return columns

    def _get_columns_for_foreign_keys(self) -> List[QbColumn[NewQbDimension]]:
        columns = []
        for col in self.cube.get_columns_of_dsd_type(NewQbDimension):
            if col.structural_definition.code_list is not None and isinstance(
                col.structural_definition.code_list,
                (NewQbCodeList, NewQbCodeListInCsvW),
            ):
                columns.append(col)

        return columns

    def _get_table_references_needed_for_foreign_keys(self) -> List[dict]:
        tables = []
        for col in self._get_columns_for_foreign_keys():
            code_list = col.structural_definition.code_list
            if isinstance(code_list, NewQbCodeList):
                _logger.debug("Referencing dataset-local code list %s.", code_list)

                tables.append(
                    {
                        "url": f"{code_list.metadata.uri_safe_identifier}.csv",
                        "tableSchema": f"{code_list.metadata.uri_safe_identifier}.table.json",
                        "suppressOutput": True,
                    }
                )
            elif isinstance(code_list, NewQbCodeListInCsvW):
                _logger.debug(
                    "Referencing legacy dataset-local code list %s with assumed table schema.",
                    code_list,
                )

                tables.append(
                    {
                        "url": code_list.csv_file_relative_path_or_uri,
                        # n.b. the below tableSchema works for *both* standard and composite legacy code lists
                        # due to the `notation` column supporting both `Notation` *and* `URI` as column titles.
                        "tableSchema": "https://gss-cogs.github.io/family-schemas/codelist-schema.json",
                        "suppressOutput": True,
                    }
                )
            else:
                raise TypeError(f"Unmatched codelist type {type(code_list)}")

        return tables

    def _generate_foreign_keys_for_cube(self) -> List[dict]:
        foreign_keys: List[dict] = []
        for col in self._get_columns_for_foreign_keys():
            code_list = col.structural_definition.code_list
            if isinstance(code_list, NewQbCodeList):
                _logger.debug(
                    "Configuring foreign key constraints for dataset-local code list %s",
                    code_list,
                )
                foreign_keys.append(
                    {
                        "columnReference": csvw_column_name_safe(
                            col.uri_safe_identifier
                        ),
                        "reference": {
                            "resource": f"{code_list.metadata.uri_safe_identifier}.csv",
                            "columnReference": "uri_identifier",
                        },
                    }
                )
            elif isinstance(code_list, NewQbCodeListInCsvW):
                _logger.debug(
                    "Configuring foreign key constraints for legacy dataset-local code list %s",
                    code_list,
                )

                foreign_keys.append(
                    {
                        "columnReference": csvw_column_name_safe(
                            col.uri_safe_identifier
                        ),
                        "reference": {
                            "resource": code_list.csv_file_relative_path_or_uri,
                            "columnReference": "notation",  # NewQbCodeListInCsvW are used for historic reasons and they always use the notation key for their primary key. External users cannot create NewQbCodeListInCsvW.
                        },
                    }
                )
            else:
                raise TypeError(f"Unmatched codelist type {type(code_list)}")

        return foreign_keys

    def _generate_virtual_columns_for_obs_val_in_pivoted_shape_cube(
        self, obs_column: QbColumn[QbObservationValue]
    ) -> List[dict]:
        _logger.debug(
            "Generating virtual columns for obs val col '%s' in pivoted shape cube",
            obs_column.csv_column_title,
        )

        virtual_columns: List[dict] = []

        observation_uri = self._uris.get_observation_uri_for_pivoted_shape_data_set(
            obs_column
        )
        csvw_safe_obs_column_name = csvw_column_name_safe(obs_column.csv_column_title)
        measure = obs_column.structural_definition.measure
        assert measure is not None

        # Creates a virtual col for `?sliceUri qb:observation ?obsUri`
        virtual_columns.append(
            {
                "name": f"virt_obs_{csvw_safe_obs_column_name}",
                "virtual": True,
                "propertyUrl": "qb:Observation",
                "valueUrl": observation_uri,
            }
        )
        # Creates a virtual col for `?obsUri qb:measureType ?measureUri`
        virtual_columns.append(
            {
                "name": f"virt_obs_{csvw_safe_obs_column_name}_meas",
                "virtual": True,
                "aboutUrl": observation_uri,
                "propertyUrl": "qb:measureType",
                "valueUrl": self._uris.get_measure_uri(measure),
            }
        )
        # For each dimension in the cube, creates the `?obsUri ?dimUri ?valueUri` triple.
        dimension_columns = self.cube.get_columns_of_dsd_type(QbDimension)
        for dimension_col in dimension_columns:
            _logger.debug(
                "Generating virtual column for dimension column with title '%s'",
                dimension_col.csv_column_title,
            )
            (
                property_url,
                value_url,
            ) = self._get_default_property_value_uris_for_dimension(dimension_col)

            if dimension_col.csv_column_uri_template is not None:
                _logger.debug(
                    "Dimension column with title '%s'has a csv column uri template defined",
                    dimension_col.csv_column_title,
                )
                value_url = dimension_col.csv_column_uri_template

            virtual_columns.append(
                {
                    "name": (
                        f"virt_dim_{csvw_safe_obs_column_name}_"
                        + csvw_column_name_safe(dimension_col.csv_column_title)
                    ),
                    "virtual": True,
                    "aboutUrl": observation_uri,
                    "propertyUrl": property_url,
                    "valueUrl": value_url,
                }
            )
        # Creates the virtual column for the triple `?obsUri rdf:type qb:Observation`
        virtual_columns.append(
            {
                "name": f"virt_obs_{csvw_safe_obs_column_name}_type",
                "virtual": True,
                "aboutUrl": observation_uri,
                "propertyUrl": "rdf:type",
                "valueUrl": "qb:Observation",
            }
        )
        # Creates a virtual column for the triple `?obsUri qb:dataSet ?dataSetUri`
        virtual_columns.append(
            {
                "name": f"virt_dataSet_{csvw_safe_obs_column_name}",
                "virtual": True,
                "aboutUrl": observation_uri,
                "propertyUrl": "qb:dataSet",
                "valueUrl": self._uris.get_dataset_uri(),
            }
        )

        return virtual_columns

    def _generate_virtual_columns_for_obs_vals_in_pivoted_shape_cube(
        self,
    ) -> List[Dict[str, Any]]:
        _logger.debug("Generating virtual columns for pivoted shape cube")

        virtual_columns: List[dict] = []

        # Generates the virtual column defining the `?sliceUri rdf:type qb:Slice` triple.
        virtual_columns.append(
            {
                "name": "virt_slice",
                "virtual": True,
                "propertyUrl": "rdf:type",
                "valueUrl": "qb:Slice",
            }
        )

        # Generates the virtual column defining the `?sliceUri qb:sliceStructure ?valueUrl` triple.
        virtual_columns.append(
            {
                "name": "virt_slice_structure",
                "virtual": True,
                "propertyUrl": "qb:sliceStructure",
                "valueUrl": self._uris.get_slice_key_across_measures_uri(),
            }
        )

        observation_value_columns = self.cube.get_columns_of_dsd_type(
            QbObservationValue
        )
        for obs_column in observation_value_columns:
            virtual_columns.extend(
                self._generate_virtual_columns_for_obs_val_in_pivoted_shape_cube(
                    obs_column
                )
            )

        return virtual_columns

    def _generate_virtual_columns_for_standard_shape_cube(self) -> List[Dict[str, Any]]:
        _logger.debug("Generating virtual columns for standard shape cube")

        virtual_columns = []
        for column in self.cube.columns:
            if isinstance(column, QbColumn):
                if isinstance(column.structural_definition, QbObservationValue):
                    _logger.debug(
                        "The column with title '%s' is an observation value column.",
                        column.csv_column_title,
                    )
                    virtual_columns += self._generate_virtual_columns_for_obs_val_in_standard_shape_cube(
                        column.structural_definition
                    )

        return virtual_columns

    def _generate_virtual_columns_for_obs_val_in_standard_shape_cube(
        self, obs_val: QbObservationValue
    ) -> List[Dict[str, Any]]:
        _logger.debug("Generating virtual columns for standard shape cube")

        virtual_columns: List[dict] = [
            {
                "name": "virt_type",
                "virtual": True,
                "propertyUrl": "rdf:type",
                "valueUrl": "http://purl.org/linked-data/cube#Observation",
            },
            {
                "name": "virt_dataset",
                "virtual": True,
                "propertyUrl": "http://purl.org/linked-data/cube#dataSet",
                "valueUrl": self._uris.get_dataset_uri(),
            },
        ]
        unit = obs_val.unit
        if unit is not None:
            _logger.debug("Adding virtual unit column.")
            virtual_columns.append(
                {
                    "name": VIRT_UNIT_COLUMN_NAME,
                    "virtual": True,
                    "propertyUrl": "http://purl.org/linked-data/sdmx/2009/attribute#unitMeasure",
                    "valueUrl": self._uris.get_unit_uri(unit),
                }
            )

        return virtual_columns

    def _get_writer_for_code_list(self, code_list) -> SkosCodeListWriter:
        return SkosCodeListWriter(code_list, self.cube.uri_style)

    def _generate_csvqb_column(self, column: CsvColumn) -> Dict[str, Any]:
        _logger.debug(
            "Generating CSV-W Column Definition for '%s'", column.csv_column_title
        )

        csvw_col: Dict[str, Any] = {
            "titles": column.csv_column_title,
            "name": csvw_column_name_safe(column.uri_safe_identifier),
        }

        if isinstance(column, SuppressedCsvColumn):
            csvw_col["suppressOutput"] = True
            _logger.debug("'%s' is a suppressed column", column.csv_column_title)
        elif isinstance(column, QbColumn):
            self._define_csvw_column_for_qb_column(csvw_col, column)
        else:
            raise TypeError(
                f"Unhandled column type ({type(column)}) with title '{column.csv_column_title}'"
            )

        return csvw_col

    def _determine_whether_the_column_is_required(self, column: QbColumn) -> bool:
        return (
            isinstance(
                column.structural_definition,
                (QbDimension, QbMultiUnits, QbMultiMeasureDimension),
            )
            or (
                isinstance(column.structural_definition, QbAttribute)
                and column.structural_definition.get_is_required()
            )
            or (
                isinstance(column.structural_definition, QbObservationValue)
                and len(get_observation_status_columns(self.cube)) == 0
                # We cannot mark an observation value column as `required` if there are `obsStatus` columns defined
                # since we permit missing observation values where an `obsStatus` explains the reason.
            )
        )

    def _define_csvw_column_for_qb_column(
        self, csvw_col: dict, column: QbColumn
    ) -> None:
        _logger.debug(
            "Expanding CSV-W column definition for DSD column '%s' (%s).",
            column.csv_column_title,
            column.structural_definition.__class__.__name__,
        )

        # If the cube is in pivoted shape, check what the column represents to set the aboutUrl
        if self.cube.is_pivoted_shape:
            about_url = self._uris.get_about_url_for_csvw_col_in_pivoted_shape_cube(
                column
            )
            _logger.debug(
                "About url for column with tile '%s' is '%s'",
                about_url,
                column.csv_column_title,
            )
            if about_url is not None:
                csvw_col["aboutUrl"] = about_url

        (
            property_url,
            default_value_url,
        ) = self._get_default_property_value_uris_for_column(column)

        _logger.debug(
            "Column has default propertyUrl '%s' and default valueUrl '%s'.",
            property_url,
            default_value_url,
        )

        if property_url is not None:
            csvw_col["propertyUrl"] = property_url

        if column.csv_column_uri_template is not None:
            # User-specified value overrides our default guess.
            csvw_col["valueUrl"] = column.csv_column_uri_template
        elif isinstance(column.structural_definition, QbAttributeLiteral):
            _logger.debug("Column valueUrl is left unset.")
            pass
        elif default_value_url is not None:
            csvw_col["valueUrl"] = default_value_url

        if isinstance(column.structural_definition, QbObservationValue):
            _logger.debug(
                "Setting CSV-W datatype to %s.", column.structural_definition.data_type
            )
            csvw_col["datatype"] = column.structural_definition.data_type
        elif isinstance(column.structural_definition, QbAttributeLiteral):
            _logger.debug(
                "Setting CSV-W datatype to %s.", column.structural_definition.data_type
            )
            csvw_col["datatype"] = column.structural_definition.data_type

        is_required = self._determine_whether_the_column_is_required(column)
        if is_required:
            _logger.debug("Column is required.")
        else:
            _logger.debug("Column is not required.")

        csvw_col["required"] = is_required

    def _get_default_property_value_uris_for_multi_units(
        self, column: QbColumn[QbMultiUnits]
    ) -> Tuple[str, str]:
        unit_value_uri = self._uris.get_unit_column_unit_template_uri(column)

        return (
            "http://purl.org/linked-data/sdmx/2009/attribute#unitMeasure",
            unit_value_uri,
        )

    def _get_default_property_value_uris_for_multi_measure(
        self, column: QbColumn[QbMultiMeasureDimension]
    ) -> Tuple[str, str]:
        measure_value_uri = (
            self._uris.get_measure_dimension_column_measure_template_uri(column)
        )

        return "http://purl.org/linked-data/cube#measureType", measure_value_uri

    def _get_default_property_value_uris_for_column(
        self, column: QbColumn
    ) -> Tuple[Optional[str], Optional[str]]:
        _logger.debug(
            "Getting default property value uris for column with title '%s'",
            column.csv_column_title,
        )

        if isinstance(column.structural_definition, QbDimension):
            _logger.debug("Column is a dimension column")
            return self._get_default_property_value_uris_for_dimension(column)
        elif isinstance(column.structural_definition, QbAttribute):
            _logger.debug("Column is an attribute column")
            return self._get_default_property_value_uris_for_attribute(column)
        elif isinstance(column.structural_definition, QbMultiUnits):
            _logger.debug("Column is a multi-units column")
            return self._get_default_property_value_uris_for_multi_units(column)
        elif isinstance(column.structural_definition, QbMultiMeasureDimension):
            _logger.debug("Column is a multi-measure dimension column")
            return self._get_default_property_value_uris_for_multi_measure(column)
        elif isinstance(column.structural_definition, QbObservationValue):
            _logger.debug("Column is an observation value column")
            return self._get_default_property_value_uris_for_observation_value(
                column.structural_definition
            )
        else:
            raise TypeError(
                f"Unhandled component type {type(column.structural_definition)}"
            )

    def _get_default_property_value_uris_for_dimension(
        self, column: QbColumn[QbDimension]
    ) -> Tuple[str, Optional[str]]:
        dimension = column.structural_definition
        dimension_uri = self._uris.get_dimension_uri(dimension)
        if isinstance(dimension, ExistingQbDimension):
            return (
                dimension_uri,
                self._uris.get_column_uri_template_fragment(column),
            )
        elif isinstance(dimension, NewQbDimension):
            value_uri = self._uris.get_column_uri_template_fragment(column)
            if dimension.code_list is None:
                _logger.debug(
                    "Dimension does not have code list; valueUrl defaults directly to column's value."
                )
            else:
                _logger.debug(
                    "Dimension valueUrl determined by code list %s.",
                    dimension.code_list,
                )
                value_uri = self._uris.get_default_value_uri_for_code_list_concepts(
                    column, dimension.code_list
                )
            return dimension_uri, value_uri
        else:
            raise TypeError(f"Unhandled dimension type {type(dimension)}")

    def _get_default_property_value_uris_for_attribute(
        self, column: QbColumn[QbAttribute]
    ) -> Tuple[str, str]:
        attribute = column.structural_definition
        column_uri_fragment = self._uris.get_column_uri_template_fragment(column)
        value_uri = self._uris.get_column_uri_template_fragment(column)

        attribute_uri = self._uris.get_attribute_uri(attribute)

        if isinstance(attribute, ExistingQbAttribute):
            if len(attribute.new_attribute_values) > 0:
                _logger.debug(
                    "Existing Attribute has new attribute values which define the valueUrl."
                )
                # NewQbAttributeValues defined here.
                value_uri = self._new_uri_helper.get_attribute_value_uri(
                    column.uri_safe_identifier, column_uri_fragment
                )
            else:
                _logger.debug("Existing Attribute does not have new attribute values.")

            # N.B. We can't do mix-and-match New/Existing attribute values.

            return attribute_uri, value_uri
        elif isinstance(attribute, NewQbAttribute):
            if len(attribute.new_attribute_values) > 0:
                _logger.debug(
                    "New Attribute has new attribute values which define the valueUrl."
                )
                # NewQbAttributeValues defined here.
                value_uri = self._uris.get_new_attribute_value_uri(
                    attribute.uri_safe_identifier, column_uri_fragment
                )
            else:
                _logger.debug("New Attribute does not have new attribute values.")

            # N.B. We can't do mix-and-match New/Existing attribute values.

            return attribute_uri, value_uri
        else:
            raise TypeError(f"Unhandled attribute type {type(attribute)}")

    def _get_default_property_value_uris_for_observation_value(
        self,
        observation_value: QbObservationValue,
    ):
        if observation_value.is_pivoted_shape_observation:
            assert observation_value.measure is not None
            _logger.debug(
                "Single-measure observation value propertyUrl defined by measure %s",
                observation_value.measure,
            )
            return self._uris.get_measure_uri(observation_value.measure), None
        else:
            # In the standard shape
            multi_measure_dimension_col = self._get_single_column_of_type(
                QbMultiMeasureDimension
            )
            _logger.debug(
                "Multi-measure observation value propertyUrl defined by measure column %s",
                multi_measure_dimension_col.csv_column_title,
            )

            measure_uri_template = (
                self._uris.get_measure_dimension_column_measure_template_uri(
                    multi_measure_dimension_col
                )
            )
            return measure_uri_template, None

    def _get_single_column_of_type(
        self, t: Type[QbColumnarDsdType]
    ) -> QbColumn[QbColumnarDsdType]:
        cols = self.cube.get_columns_of_dsd_type(t)
        if len(cols) != 1:
            raise ValueError(
                f"Found {len(cols)} columns with component type {t} in cube. Expected 1."
            )
        return cols[0]

    def _get_primary_key_columns(self) -> List[str]:
        dimension_columns: Iterable[QbColumn] = itertools.chain(
            self.cube.get_columns_of_dsd_type(QbDimension),
            self.cube.get_columns_of_dsd_type(QbMultiMeasureDimension),
        )

        primary_key_columns = [
            csvw_column_name_safe(c.csv_column_title) for c in dimension_columns
        ]

        _logger.debug("Primary key columns are %s", primary_key_columns)
        return primary_key_columns
