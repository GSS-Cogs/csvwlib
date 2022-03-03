"""
Config.json Loader
__________________

A loader for the config.json.
"""
import json
import logging

from typing import Dict, Tuple

from urllib.parse import urlsplit

import pandas as pd
from jsonschema.exceptions import ValidationError
from csvcubed.readers.v1_0.columnschema import *

from csvcubed.models.cube import *
from csvcubed.readers.v1_0.mapcolumntocomponent import map_column_to_qb_component
from csvcubed.utils.dict import get_with_func_or_none
from csvcubed.utils.uri import uri_safe
from csvcubed.utils.json import load_json_from_uri, read_json_from_file
from csvcubed.utils.validators.schema import validate_dict_against_schema
from csvcubedmodels.rdf.namespaces import GOV


# Used to determine whether a column name matches accepted conventions
CONVENTION_NAMES = {
    "measures": [
        "measure",
        "measures",
        "measures column",
        "measure column",
        "measure type",
        "measure types",
    ],
    "observations": [
        "observation",
        "observations",
        "obs",
        "values",
        "value",
        "val",
        "vals",
    ],
    "units": ["unit", "units", "units column", "unit column", "unit type", "unit types"]
}

log = logging.getLogger(__name__)


def _load_resource(resource_path: Path) -> dict:
    """
    Load a json schema document from either a File or URI
    """
    schema: dict = {}

    if "http" in urlsplit(str(resource_path)).scheme:
        schema = load_json_from_uri(resource_path)

    else:
        schema = read_json_from_file(resource_path)

    return schema


def _override_catalog_metadata_state(
    catalog_metadata_json_file: Path, cube: QbCube
) -> None:
    with open(catalog_metadata_json_file, "r") as f:
        catalog_metadata_dict: dict = json.load(f)
    overriding_catalog_metadata = CatalogMetadata.from_dict(catalog_metadata_dict)
    cube.metadata.override_with(
        overriding_catalog_metadata,
        overriding_keys={k for k in catalog_metadata_dict.keys()},
    )


def _from_config_json_dict(data: pd.DataFrame,
                           config: Optional[Dict],
                           json_parent_dir: Path
                           ) -> QbCube:
    columns: List[QbColumn] = []
    if not config:
        metadata: CatalogMetadata = _metadata_from_dict({})
    else:
        metadata: CatalogMetadata = _metadata_from_dict(config)
        for column_title in config.get('columns', []):
            column_config = config['columns'].get(column_title)

            # When the config json contains a col definition and the col title is not in the data
            if column_title not in data.columns:
                column_data = None if column_title not in data.columns else data[column_title]

            columns.append(
                    map_column_to_qb_component(column_title,
                                               column_config,
                                               column_data,
                                               json_parent_dir)
                )

    return Cube(metadata, data, columns)


def _metadata_from_dict(config: dict) -> "CatalogMetadata":
    creator = get_with_func_or_none(config, "creator", lambda c: str(GOV[uri_safe(c)]))
    publisher = get_with_func_or_none(config, "publisher", lambda p: str(GOV[uri_safe(p)]))
    themes = config.get('themes', "")
    if isinstance(themes, str) and themes:
        themes = [themes]
    keywords = config.get('keywords', "")
    if isinstance(keywords, str) and keywords:
        keywords = [keywords]

    return CatalogMetadata(
        identifier=config.get("id"),
        title=config.get("title"),
        description=config.get("description", ""),
        summary=config.get("summary", ""),
        creator_uri=creator,
        publisher_uri=publisher,
        public_contact_point_uri=config.get('public_contact_point'),
        dataset_issued=config.get('dataset_issued'),
        dataset_modified=config.get('dataset_modified'),
        license_uri=config.get('license'),
        theme_uris=[uri_safe(t) for t in themes if t] if isinstance(themes, list) else None,
        keywords=keywords if isinstance(keywords, list) else None,
        spatial_bound_uri=uri_safe(config['spatial_bound'])
            if config.get('spatial_bound') else None,
        temporal_bound_uri=uri_safe(config['temporal_bound'])
            if config.get('temporal_bound') else None,
        uri_safe_identifier_override=config['id'] if config.get('id') else None
    )


# def get_cube_from_data(csv_path: Path) -> QbCube:
#     """
#     Given a Pandas DataFrame, it resolves each column to a column based on naming conventions
#     The cube must have dimension, observation, units and measures columns
#     The csv_path arg is used for the Cube title
#     """
#     data: pd.DataFrame = pd.read_csv(csv_path)
#     if data.shape[0] < 2:
#         # Must have 2 or more rows, a heading row and a data row
#         raise ValueError("The csv data did not contain sufficient rows to continue")
#
#     elif data.shape[1] < 3:
#         # Must have 3 or more columns, 1+ dimension, 1 observation, 1 attribute,
#         raise ValueError("The csv did not contain sufficient columns to continue")
#
#     # Iterate over the column names and count the type for each
#     convention_col_counts = {
#         "dimension": 0,
#         "observations": 0,
#         "measures": 0,
#         "units": 0,
#         "attribute": 0,
#     }
#     cube_columns: List[QbColumn] = []
#     column_types: List[str] = []
#     for i, column_name in enumerate(data.columns):
#         # Determine column type by matching column names accepted by convention or default to 'dimension'
#         convention_name_matches = [
#             standard_name
#             for standard_name, options in CONVENTION_NAMES.items()
#             if column_name.lower() in options
#         ]
#         column_type = (
#             convention_name_matches[0] if convention_name_matches else "dimension"
#         )
#         column_types.append(column_type)
#         convention_col_counts[column_type] += 1
#
#     #  Check we have the pre-requisite columns
#     if convention_col_counts["dimension"] < 1:
#         raise ValueError("The data does not contain any dimension columns")
#     if convention_col_counts["observations"] < 1:
#         raise ValueError("The data does not contain any observation columns")
#     if convention_col_counts["attribute"] < 0:
#         raise ValueError("The data does not contain any attribute columns")
#     if convention_col_counts["measures"] < 1:
#         raise ValueError("The data does not contain any measure columns")
#     if convention_col_counts["units"] < 1:  # needs resolving between Rob and Andrew
#         raise ValueError("The data does not contain any attribute columns")
#
#     for i, column_type in enumerate(column_types):
#         # Build a dict of fields for the identified column types' data-class
#         column_name = data.columns[i]
#         column_data = data.T.iloc[i]
#
#         if column_type == "dimension":
#             column_dict = {
#                 "type": column_type,
#                 "label": column_name,
#                 "code_list": True
#             }
#
#         elif column_type == "observations":
#             column_dict = {
#                 "type": column_type,
#                 "value": column_name,
#                 "datatype": "decimal",
#             }
#
#         elif column_type in ["measures", "units"]:
#             column_dict = {
#                 "type": column_type
#             }
#         elif column_type == "attribute":
#             # Note: attribute type columns are currently not supported
#             raise ValueError(
#                 "Column type 'Attribute' is not supported when using csv naming convention"
#             )
#
#         else:
#             raise ValueError(f"Column type '{column_type}' is not supported.")
#
#         # As all columns will be new in this scenario get a pd.Series for the column
#
#         try:
#             qb_column = map_column_to_qb_component(
#                 column_title=column_name,
#                 column=column_dict,
#                 data=column_data.astype("category"),
#                 json_parent_dir=csv_path.parent.absolute(),
#             )
#             cube_columns.append(qb_column)
#
#         except Exception as err:
#             import traceback
#             traceback.print_exc()
#             log.error(f"{type(err)} exception raised because: {repr(err)}")
#
#     cube_metadata = _metadata_from_dict(
#         {"id": str(csv_path).upper(), "title": csv_path.name.upper().replace("_", " ")}
#     )
#     # TODO - Create the new Cube
#     cube = Cube(metadata=cube_metadata, data=data, columns=cube_columns)
#     # validation_errors = cube.validate()
#     validation_errors = cube.pydantic_validation()
#
#     return cube, validation_errors


def get_cube_from_config_json(
        csv_path: Path,
        config_path: Optional[Path]

) -> Tuple[QbCube, List[ValidationError]]:
    """
    Generates a Cube structure from a config.json input.
    :return: tuple of cube and json schema errors (if any)
    """
    data: pd.DataFrame = pd.read_csv(csv_path)

    # If we have a config json file then load it and validate against its reference schema
    if config_path:
        config = _load_resource(config_path.resolve())
        schema = _load_resource(Path(config['$schema']).resolve())
        try:
            errors = validate_dict_against_schema(value=config, schema=schema)
            if errors:
                return None, errors

        except Exception as err:
            print(err)
    else:
        config = None

    parent_path = csv_path.parent if not config_path else config_path.parent
    cube = _from_config_json_dict(data, config, parent_path)

    # Update metadata from csv where appropriate
    cube.metadata.title = cube.metadata.title \
        if cube.metadata.title \
        else  csv_path.name.upper().replace("_", " ")

    # Update columns from csv where appropriate, i.e. config did not define the column
    for i, column_title in enumerate(data.columns):
        # ... determine if the column_title in data matches a convention
        if column_title not in [col.csv_column_title for col in cube.columns]:
            convention_names = [standard_name for standard_name, options in CONVENTION_NAMES.items()
            if column_title.lower() in options
            ]

            # ... get or default the column type
            column_type = (
                convention_names[0] if convention_names else "dimension"
            )

            # ... create a default config dict for the column type
            if column_type == "dimension":
                column_dict = {
                    "type": column_type,
                    "label": column_title,
                    "code_list": True
                }

            elif column_type == "observations":
                column_dict = {
                    "type": column_type,
                    "value": column_title,
                    "datatype": "decimal",
                }

            elif column_type in ["measures", "units"]:
                column_dict = {
                    "type": column_type
                }
            elif column_type == "attribute":
                # Note: attribute type columns are currently not supported for getting from data
                raise ValueError(
                    "Column type 'Attribute' is not supported when using csv naming convention"
                )

            else:
                raise ValueError(f"Column type '{column_type}' is not supported.")

            try:
                qb_column = map_column_to_qb_component(
                    column_title=column_title,
                    column=column_dict,
                    data=data[column_title].astype("category"),
                    json_parent_dir=csv_path.parent.absolute(),
                )
                if i < len(cube.columns):
                    cube.columns.insert(i, qb_column)
                else:
                    cube.columns.append(qb_column)

            except Exception as err:
                import traceback
                traceback.print_exc()
                log.error(f"{type(err)} exception raised because: {repr(err)}")
                raise err

    return cube, []


if __name__ == "__main__":
    log.error(
        "The config deserialiser module should not be run directly, please user the 'csvcubed build' command."
    )
