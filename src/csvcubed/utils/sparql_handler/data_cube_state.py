from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import Dict, List, Any

import rdflib

from csvcubed.models.cube.cube_shape import CubeShape
from csvcubed.models.sparqlresults import (
    ColTitlesAndNamesResult,
    CsvUrlResult,
    CubeTableIdentifiers,
    ObservationValueColumnTitleAboutUrlResult,
    QubeComponentResult,
    QubeComponentsResult,
    UnitColumnAboutValueUrlResult,
    IsPivotedShapeMeasureResult,
)
from csvcubed.utils.dict import (
    get_from_dict_ensure_exists,
)  # Use this instead of _get_value_for_key
from csvcubed.utils.iterables import group_by, first
from csvcubed.utils.sparql_handler.sparqlquerymanager import (
    select_col_titles_and_names,
    select_csvw_dsd_qube_components,
    select_data_set_dsd_and_csv_url,
    select_observation_value_column_title_and_about_url,
    select_qb_csv_url,
    select_unit_col_about_value_urls,
    select_is_pivoted_shape_for_measures_in_data_set,
)


@dataclass
class DataCubeState:
    rdf_graph: rdflib.ConjunctiveGraph
    csvw_json_path: Path

    """
    Private utility functions.
    """
    # Use existing function from csvcubed.utils.dict
    def _get_value_for_key(self, key: str, dict: Dict) -> Any:
        maybe_value = dict.get(key)
        if maybe_value is None:
            raise KeyError(f"Could not find the definition for key '{key}'")
        return maybe_value

    """
    Private cached properties.
    """

    @cached_property
    def _unit_col_about_value_urls(
        self,
    ) -> Dict[str, List[UnitColumnAboutValueUrlResult]]:
        """
        Queries and caches unit column about and value urls.
        """
        results = select_unit_col_about_value_urls(self.rdf_graph)
        return group_by(results, lambda r: r.csv_url)

    @cached_property
    def _obs_val_col_titles_about_urls(
        self,
    ) -> Dict[str, List[ObservationValueColumnTitleAboutUrlResult]]:
        """
        Queries and caches observation value column titles and about urls.
        """
        results = select_observation_value_column_title_and_about_url(self.rdf_graph)
        return group_by(results, lambda r: r.csv_url)

    @cached_property
    def _col_names_col_titles(self) -> Dict[str, List[ColTitlesAndNamesResult]]:
        """
        Queries and caches column names and titles.
        """
        results = select_col_titles_and_names(self.rdf_graph)
        return group_by(results, lambda r: r.csv_url)

    @cached_property
    def _select_qb_csv_url(self) -> Dict[str, List[CsvUrlResult]]:
        """ """
        results = select_qb_csv_url(self.rdf_graph)
        return group_by(results, lambda r: r.csv_url)

    @cached_property
    def _cube_table_identifiers(self) -> Dict[str, CubeTableIdentifiers]:
        """
        Identifiers linking a given qb:DataSet with a csvw table (identified by the csvw:url).

        Maps from csv_url to the identifiers.
        """
        results = select_data_set_dsd_and_csv_url(self.rdf_graph)
        results_dict: Dict[str, CubeTableIdentifiers] = {}
        for result in results:
            results_dict[result.csv_url] = result
        return results_dict

    @cached_property
    def _dsd_qube_components(self) -> Dict[str, List[QubeComponentResult]]:
        """
        Queries and caches qube components
        """
        result = select_csvw_dsd_qube_components(self.rdf_graph, self.csvw_json_path)
        map_dsd_uri_to_csv_url = {
            i.dsd_uri: i.csv_url for i in self._cube_table_identifiers.values()
        }
        return group_by(
            result.qube_components, lambda c: map_dsd_uri_to_csv_url[c.dsd_uri]
        )

    @cached_property
    def _cube_shapes(self) -> Dict[str, CubeShape]:
        """
        A mapping of csvUrl to the given CubeShape. CSV tables which aren't cubes are not present here.
        """

        def _detect_shape_for_cube(
            measures_with_shape: List[IsPivotedShapeMeasureResult],
        ) -> CubeShape:
            """
            Given a metadata validator as input, returns the shape of the cube that metadata describes (Pivoted or
            Standard).
            """
            all_pivoted = True
            all_standard_shape = True
            for measure in measures_with_shape:
                all_pivoted = all_pivoted and measure.is_pivoted_shape
                all_standard_shape = all_standard_shape and not measure.is_pivoted_shape

            if all_pivoted:
                return CubeShape.Pivoted
            elif all_standard_shape:
                return CubeShape.Standard
            else:
                raise TypeError(
                    "The input metadata is invalid as the shape of the cube it represents is not supported. More "
                    "specifically, the input contains some observation values that are pivoted and some are not "
                    "pivoted."
                )

        results = select_is_pivoted_shape_for_measures_in_data_set(
            self.rdf_graph, list(self._cube_table_identifiers.values())
        )

        map_csv_url_to_measure_shape = group_by(results, lambda r: r.csv_url)

        return {
            csv_url: _detect_shape_for_cube(measures_with_shape)
            for (csv_url, measures_with_shape) in map_csv_url_to_measure_shape.items()
        }

    """
    Public getters for the cached properties.
    """

    def get_unit_col_about_value_urls_for_csv(
        self, csv_url: str
    ) -> List[UnitColumnAboutValueUrlResult]:
        """
        Getter for _unit_col_about_value_urls cached property.
        """
        return get_from_dict_ensure_exists(self._unit_col_about_value_urls, csv_url)

    def get_obs_val_col_titles_about_urls_for_csv(
        self, csv_url: str
    ) -> List[ObservationValueColumnTitleAboutUrlResult]:
        """
        Getter for _obs_val_col_titles_about_urls cached property.
        """
        return get_from_dict_ensure_exists(self._obs_val_col_titles_about_urls, csv_url)

    def get_col_name_col_title_for_csv(
        self, csv_url: str
    ) -> List[ColTitlesAndNamesResult]:
        """
        Getter for _col_names_col_titles cached property.
        """
        # result: List[ColTitlesAndNamesResult] = self._get_value_for_key(
        #     csv_url, self._col_names_col_titles
        # )
        # return result
        return get_from_dict_ensure_exists(self._col_names_col_titles, csv_url)

    def get_qb_csv_url(self, csv_url: str) -> List[CsvUrlResult]:
        """ """
        return get_from_dict_ensure_exists(self._select_qb_csv_url, csv_url)

    def get_cube_identifiers_for_csv(self, csv_url: str) -> CubeTableIdentifiers:
        """
        Getter for data_set_dsd_and_csv_url_for_csv_url cached property.
        """
        return get_from_dict_ensure_exists(self._cube_table_identifiers, csv_url)

    def get_cube_identifiers_for_data_set(
        self, data_set_uri: str
    ) -> CubeTableIdentifiers:
        """
        Getter for data_set_dsd_and_csv_url_for_csv_url cached property.
        """
        result = first(
            self._cube_table_identifiers.values(),
            lambda i: i.data_set_url == data_set_uri,
        )
        if result is None:
            raise KeyError(f"Could not find the data_set with URI '{data_set_uri}'.")

        return result

    def get_dsd_qube_components_for_csv(self, csv_url: str) -> QubeComponentsResult:
        """
        Getter for DSD Qube Components cached property.
        """
        components: List[QubeComponentResult] = get_from_dict_ensure_exists(
            self._dsd_qube_components, csv_url
        )
        return QubeComponentsResult(components, len(components))

    def get_shape_for_csv(self, csv_url: str) -> CubeShape:
        return get_from_dict_ensure_exists(self._cube_shapes, csv_url)
