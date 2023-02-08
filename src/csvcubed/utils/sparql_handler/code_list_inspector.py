"""This is the CodeListInspector class script"""
from dataclasses import dataclass
from functools import cached_property
from typing import List, Optional

from csvcubedmodels.rdf.namespaces import SKOS

from csvcubed.models.sparqlresults import (
    CatalogMetadataResult,
    CodeListTableIdentifers,
    ColumnDefinition,
)
from csvcubed.utils.iterables import first
from csvcubed.utils.sparql_handler.csvw_state import CsvWState


@dataclass
class CodeListInspector:
    """Fills this in"""

    csvw_state: CsvWState

    @cached_property
    def _code_list_table_identifiers(self) -> List[CodeListTableIdentifers]:
        def get_table_identifiers(
            csv_url: str,
            column_definitions: List[ColumnDefinition],
        ) -> Optional[CodeListTableIdentifers]:
            in_scheme_columns = [
                c
                for c in column_definitions
                if c.property_url == "skos:inScheme"
                or c.property_url == str(SKOS.inScheme)
            ]
            if not any(in_scheme_columns):
                return None

            if len(in_scheme_columns) == 1:
                return CodeListTableIdentifers(
                    csv_url, str(in_scheme_columns[0].value_url)
                )

            raise KeyError(f"Found multiple skos:inScheme columns in '{csv_url}'.")

        table_identifiers = [
            get_table_identifiers(csv_url, columns)
            for (csv_url, columns) in self.csvw_state.column_definitions.items()
        ]

        return [i for i in table_identifiers if i is not None]

    def get_table_identifiers_for_concept_scheme(
        self, concept_scheme_url: str
    ) -> CodeListTableIdentifers:
        identifiers = first(
            self._code_list_table_identifiers,
            lambda i: i.concept_scheme_url == concept_scheme_url,
        )

        if identifiers is None:
            raise KeyError(
                f"Could not find code list table identifiers for ConceptSchem URL: '{concept_scheme_url}'"
            )

        return identifiers

    def get_csvw_catalog_metadata(self) -> CatalogMetadataResult:
        """This function will access the catalogmetadataResult and compares the concept_sceme_url and returns the relevant value"""
        the_list = self.csvw_state.catalog_metadata

        concept_scheme_url = self._code_list_table_identifiers[0].concept_scheme_url

        for catalog_m_result in the_list:
            if catalog_m_result.dataset_uri == concept_scheme_url:
                return catalog_m_result

        raise ValueError(
            f"None of the results can be associated with the {concept_scheme_url}"
        )
