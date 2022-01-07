"""
Code Lists
----------

Represent code lists in an RDF Data Cube.
"""
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List, Set, Generic, TypeVar
from abc import ABC
from pandas import Series, DataFrame
from pydantic import root_validator

from .concept import NewQbConcept, DuplicatedQbConcept
from csvcubed.readers.skoscodelistreader import extract_code_list_concept_scheme_info
from csvcubed.utils.pandas import ensure_no_uri_safe_collision
from .arbitraryrdf import (
    ArbitraryRdf,
    RdfSerialisationHint,
    TripleFragmentBase,
)
from .datastructuredefinition import (
    SecondaryQbStructuralDefinition,
)
from csvcubed.models.cube.qb.catalog import CatalogMetadata
from csvcubed.utils.validators.uri import validate_uri
from csvcubed.utils.validators.file import validate_file_exists
from csvcubed.inputs import PandasDataTypes, pandas_input_to_columnar_str
from csvcubed.models.validationerror import ValidationError


@dataclass
class QbCodeList(SecondaryQbStructuralDefinition, ABC):
    pass


@dataclass
class ExistingQbCodeList(QbCodeList):
    """
    Contains metadata necessary to link a dimension to an existing skos:ConceptScheme.
    """

    concept_scheme_uri: str

    _concept_scheme_uri_validator = validate_uri("concept_scheme_uri")


@dataclass
class NewQbCodeListInCsvW(QbCodeList):
    """
    Contains the reference to an existing skos:ConceptScheme defined in a CSV-W.
    """

    schema_metadata_file_path: Path
    csv_file_relative_path_or_uri: str = field(init=False, repr=False)
    concept_scheme_uri: str = field(init=False, repr=False)
    concept_template_uri: str = field(init=False, repr=False)

    _schema_metadata_file_path_validator = validate_file_exists(
        "schema_metadata_file_path"
    )

    @root_validator(pre=True)
    def _csvw_contains_sufficient_information_validator(cls, values: dict) -> dict:
        csv_path = values.get("csv_file_relative_path_or_uri")
        cs_uri = values.get("concept_scheme_uri")
        c_template_uri = values.get("concept_template_uri")
        if csv_path is None or cs_uri is None or c_template_uri is None:
            schema_metadata_file_path = values["schema_metadata_file_path"]
            # The below should throw an exception if there is any problem with the CSV-W.
            extract_code_list_concept_scheme_info(schema_metadata_file_path)

            # if there's no exception but the values aren't set, something weird has happened.
            raise ValueError(
                f"'csv_file_relative_path_or_uri', 'concept_scheme_uri' or 'concept_template_uri' values are missing, "
                f"however the CSV-W seems to contain the relevant information."
            )
        return values

    def __post_init__(self):
        try:
            (
                csv_url,
                cs_uri,
                concept_template_uri,
            ) = extract_code_list_concept_scheme_info(self.schema_metadata_file_path)
            self.csv_file_relative_path_or_uri = csv_url
            self.concept_scheme_uri = cs_uri
            self.concept_template_uri = concept_template_uri
        except Exception:
            # Validation errors will be highlighted later in custom validation function.
            self.csv_file_relative_path_or_uri = None  # type: ignore
            self.concept_scheme_uri = None  # type: ignore
            self.concept_template_uri = None  # type: ignore


TNewQbConcept = TypeVar("TNewQbConcept", bound=NewQbConcept, covariant=True)


@dataclass
class NewQbCodeList(QbCodeList, ArbitraryRdf, Generic[TNewQbConcept]):
    """
    Contains the metadata necessary to create a new skos:ConceptScheme which is local to a dataset.
    """

    metadata: CatalogMetadata
    concepts: List[TNewQbConcept]
    arbitrary_rdf: List[TripleFragmentBase] = field(default_factory=list, repr=False)

    @staticmethod
    def from_data(metadata: CatalogMetadata, data: PandasDataTypes) -> "NewQbCodeList":
        columnar_data = pandas_input_to_columnar_str(data)
        concepts = [NewQbConcept(c) for c in sorted(set(columnar_data))]
        return NewQbCodeList(metadata, concepts)

    def get_permitted_rdf_fragment_hints(self) -> Set[RdfSerialisationHint]:
        return {
            RdfSerialisationHint.CatalogDataset,
            RdfSerialisationHint.ConceptScheme,
        }

    def get_default_node_serialisation_hint(self) -> RdfSerialisationHint:
        return RdfSerialisationHint.ConceptScheme

    def validate_data(self, data: PandasDataTypes) -> list[Optional[ValidationError]]:
        """
        Validate the data held in the codelists, assuming case insensitivity
        """

        errors = list()

        if isinstance(data, Series):
            errors += ensure_no_uri_safe_collision(data=data, series_name=None)
        elif isinstance(data, DataFrame):
            errors += ensure_no_uri_safe_collision(data.squeeze(), series_name=None)

        return errors


@dataclass
class CompositeQbCodeList(NewQbCodeList[DuplicatedQbConcept]):
    """Represents a :class:`NewQbCodeList` made from a set of :class:`DuplicatedQbConcept` instances."""

    variant_of_uris: List[str] = field(default_factory=list)
