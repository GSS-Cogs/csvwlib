"""
CodeList
-----------

Utilities for skos:codelists
"""

from enum import Enum
from typing import List
from csvcubed.models.csvcubedexception import InvalidNumberOfRecordsException
import pandas as pd
import numpy as np

from treelib import Node, Tree

from csvcubed.models.inspectsparqlresults import CodelistColumnResult


class CodelistPropertyUrl(Enum):
    """
    The codelist column property url types.
    """

    RDFLabel = "rdfs:label"

    SkosNotation = "skos:notation"

    SkosBroader = "skos:broader"

    SortPriority = "http://www.w3.org/ns/ui#sortPriority"

    RDFsComment = "rdfs:comment"

    SkosInScheme = "skos:inScheme"

    RDFType = "rdf:type"


def get_codelist_col_title_by_property_uri(
    columns: List[CodelistColumnResult], property_url: CodelistPropertyUrl
) -> str:
    results = [
        column for column in columns if column.column_property_url == property_url.value
    ]
    
    if len(results) != 1:
        raise InvalidNumberOfRecordsException(
            excepted_num_of_records=1, num_of_records=len(results)
        )
    
    return results[0].column_title


def build_codelist_hierarchy_tree(
    concepts_df: pd.DataFrame,
    parent_notation_col_name: str,
    label_col_name: str,
    notation_col_name: str,
) -> Tree:
    """
    TODO
    """

    tree = Tree()
    tree.create_node("root", identifier="root")
    
    # Replacing empty values with None and sorting consepts by Sort Priortiy to maintain the order when iterating below.
    concepts_df = concepts_df.replace({np.nan: None}).sort_values(by="Sort Priority")

    for _, concept_row in concepts_df.iterrows():
        node_id =  concept_row[notation_col_name]
        node_label =  concept_row[label_col_name]
        node_parent_id = concept_row[parent_notation_col_name] or "root"
        tree.create_node(node_label, identifier=node_id, parent=node_parent_id)
    
    return tree
