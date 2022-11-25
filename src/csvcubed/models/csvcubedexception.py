from abc import ABC
from enum import Enum
from pathlib import Path

from csvcubed.models.errorurl import HasErrorUrl


class CsvcubedExceptionMsges(Enum):
    """
    Error messages for the exceptions thrown in csvcubed.
    """

    InputNotSupported = "The input CSV-W json-ld is not supported. The input should be a data cube or code list generated by csvcubed."

    FailedToReadCsvwFileContent = "An error occured while reading CSV-W content from file at {csvw_metadata_file_path}"

    InvalidCsvwFileContent = "CSV-W file content is invalid."

    FailedToLoadRDFGraph = (
        "Failed to load the RDF graph from input: {csvw_metadata_file_path}"
    )

    CsvToDataFrameLoadFailed = "Failed to load CSV dataset to dataframe"

    InvalidNumberOfRecords = "Expected {excepted_num_of_records} {record_description}, but found {num_of_records}"

    FailedToReadSparqlQuery = (
        "Failed to read sparql query from file at {sparql_file_path}"
    )

    FailedToLoadTableSchemaIntoRdfGraph = (
        "Failed to load table schema '{table_schema_file}' into RDF graph"
    )

    UnsupportedComponentPropertyType = (
        "DSD component property type {property_type} is not supported"
    )

    FailedToConvertDataFrameToString = "Failed to convert dataframe to string"

    UnexpectedSparqlAskQueryResponseType = (
        "Unexpected ASK sparql query ({query_name}) response type: {response_type}"
    )

    UnexpectedSparqlAskQueryResults = "Unexpected number of results ({num_of_results}) for the {query_name} ASK sparql query"

    FeatureNotSupported = "This feature is not yet supported: {explanation}"

    ErrorProcessingDataFrame = (
        "An error occurred when performing {operation} operation on dataframe"
    )

    UnsupportedColumnDefinition = (
        "The definition for column with name {column_title} is not supported."
    )

    PrimaryKeyColumnTitleCannotBeNone = (
        "The column associated with the primary key does not contain the title."
    )

    UnsupportedNumberOfPrimaryKeyColNames = (
        "Only 1 primary key column name is supported but found {num_of_primary_key_col_names} primary key column names for the table with url {table_url}."
    )

    InvalidNumOfUnitColsForObsValColTitle = "There should be 1 unit column for the observation value column title '{obs_val_col_title}', but found {num_of_unit_cols} unit columns."

    InvalidNumOfValUrlsForAboutUrl = "There should be only 1 value url for the about url '{about_url}', but found {num_of_value_urls}."

    InvalidNumOfColsForColName = "There should be only 1 column for the column name '{column_name}', but found {num_of_cols}."

    InvalidNumOfDSDComponentsForObsValColTitle = "There should be only 1 component for the observation value column with title '{obs_val_col_title}', but found {num_of_components}."

class CsvcubedExceptionUrls(Enum):
    """
    Urls for the exceptions thrown in csvcubed.
    """

    InputNotSupported = "http://purl.org/csv-cubed/err/invalid-input"

    FailedToReadCsvwFileContent = "http://purl.org/csv-cubed/err/csvw-read"

    InvalidCsvwFileContent = "http://purl.org/csv-cubed/err/csvw-content"

    FailedToLoadRDFGraph = "http://purl.org/csv-cubed/err/rdf-load"

    FailedToLoadTableSchemaIntoRdfGraph = (
        "http://purl.org/csv-cubed/err/tbl-schema-load"
    )

    CsvToDataFrameLoadFailed = "http://purl.org/csv-cubed/err/dataframe-load"

    FailedToReadSparqlQuery = "http://purl.org/csv-cubed/err/sparql-query-read"

    UnexpectedSparqlAskQueryResponseType = "http://purl.org/csv-cubed/err/ask-response"

    UnexpectedSparqlAskQueryResults = "http://purl.org/csv-cubed/err/ask-result"

    UnsupportedComponentPropertyType = "http://purl.org/csv-cubed/err/component-type"

    InvalidNumberOfRecords = "http://purl.org/csv-cubed/err/num-records"

    ErrorProcessingDataFrame = "http://purl.org/csv-cubed/err/dataframe-process"

    FailedToConvertDataFrameToString = "http://purl.org/csv-cubed/err/dataframe-string"

    FeatureNotSupported = "http://purl.org/csv-cubed/err/feature-not-supported"

    UnsupportedColumnDefinition = (
        "http://purl.org/csv-cubed/err/column-definition-not-supported"
    )

    PrimaryKeyColumnTitleCannotBeNone = (
        "http://purl.org/csv-cubed/err/invalid-pk-col-title"
    )

    UnsupportedNumberOfPrimaryKeyColNames = (
         "http://purl.org/csv-cubed/err/unsupported-num-of-primary-keys"
    )

    InvalidNumOfUnitColsForObsValColTitle = "http://purl.org/csv-cubed/err/invalid-num-of-unit-cols-for-obs-val-col-title"

    InvalidNumOfValUrlsForAboutUrl = "http://purl.org/csv-cubed/err/invalid-num-of-value-urls-for-about-url"
    
    InvalidNumOfColsForColName = "http://purl.org/csv-cubed/err/invalid-num-of-cols-for-col-name"

    InvalidNumOfDSDComponentsForObsValColTitle = "http://purl.org/csv-cubed/err/invalid-num-of-dsd-comps-for-obs-val-col"

class CsvcubedException(Exception, HasErrorUrl, ABC):
    """Abstract class representing csvcubed exception model."""

    pass


class InputNotSupportedException(CsvcubedException):
    """Class representing the InputNotSupportedException model."""

    def __init__(self):
        super().__init__(CsvcubedExceptionMsges.InputNotSupported.value)

    @classmethod
    def get_error_url(cls) -> str:
        return CsvcubedExceptionUrls.InputNotSupported.value


class FailedToReadCsvwFileContentException(CsvcubedException):
    """Class representing the FailedToReadCsvwFileContentException model."""

    def __init__(self, csvw_metadata_file_path: Path):
        super().__init__(
            CsvcubedExceptionMsges.FailedToReadCsvwFileContent.value.format(
                csvw_metadata_file_path=str(csvw_metadata_file_path)
            )
        )

    @classmethod
    def get_error_url(cls) -> str:
        return CsvcubedExceptionUrls.FailedToReadCsvwFileContent.value


class InvalidCsvwFileContentException(CsvcubedException):
    """Class representing the InvalidCsvwFileContentException model."""

    def __init__(self):
        super().__init__(CsvcubedExceptionMsges.InvalidCsvwFileContent.value)

    @classmethod
    def get_error_url(cls) -> str:
        return CsvcubedExceptionUrls.InvalidCsvwFileContent.value


class FailedToLoadRDFGraphException(CsvcubedException):
    """Class representing the FailedToLoadRDFGraphException model."""

    def __init__(self, csvw_metadata_file_path: Path):
        super().__init__(
            CsvcubedExceptionMsges.FailedToLoadRDFGraph.value.format(
                csvw_metadata_file_path=str(csvw_metadata_file_path),
            )
        )

    @classmethod
    def get_error_url(cls) -> str:
        return CsvcubedExceptionUrls.FailedToLoadRDFGraph.value


class CsvToDataFrameLoadFailedException(CsvcubedException):
    """Class representing the CsvToDataFrameLoadFailedException model."""

    def __init__(self):
        super().__init__(CsvcubedExceptionMsges.CsvToDataFrameLoadFailed.value)

    @classmethod
    def get_error_url(cls) -> str:
        return CsvcubedExceptionUrls.CsvToDataFrameLoadFailed.value


class InvalidNumberOfRecordsException(CsvcubedException):
    """Class representing the InvalidNumberOfRecordsException model."""

    def __init__(
        self, record_description: str, excepted_num_of_records: int, num_of_records: int
    ):
        super().__init__(
            CsvcubedExceptionMsges.InvalidNumberOfRecords.value.format(
                record_description=record_description,
                excepted_num_of_records=excepted_num_of_records,
                num_of_records=num_of_records,
            )
        )

    @classmethod
    def get_error_url(cls) -> str:
        return CsvcubedExceptionUrls.InvalidNumberOfRecords.value


class FailedToReadSparqlQueryException(CsvcubedException):
    """Class representing the FailedToReadSparqlQueryException model."""

    def __init__(self, sparql_file_path: Path):
        super().__init__(
            CsvcubedExceptionMsges.FailedToReadSparqlQuery.value.format(
                sparql_file_path=str(sparql_file_path),
            )
        )

    @classmethod
    def get_error_url(cls) -> str:
        return CsvcubedExceptionUrls.FailedToReadSparqlQuery.value


class FailedToLoadTableSchemaIntoRdfGraphException(CsvcubedException):
    """Class representing the FailedToLoadTableSchemaIntoRdfGraphException model."""

    def __init__(self, table_schema_file: str):
        super().__init__(
            CsvcubedExceptionMsges.FailedToLoadTableSchemaIntoRdfGraph.value.format(
                table_schema_file=table_schema_file
            )
        )

    @classmethod
    def get_error_url(cls) -> str:
        return CsvcubedExceptionUrls.FailedToLoadTableSchemaIntoRdfGraph.value


class UnsupportedComponentPropertyTypeException(CsvcubedException):
    """Class representing the UnsupportedComponentPropertyType model."""

    def __init__(self, property_type: str):
        super().__init__(
            CsvcubedExceptionMsges.UnsupportedComponentPropertyType.value.format(
                property_type=property_type
            )
        )

    @classmethod
    def get_error_url(cls) -> str:
        return CsvcubedExceptionUrls.UnsupportedComponentPropertyType.value


class FailedToConvertDataFrameToStringException(CsvcubedException):
    """Class representing the FailedToConvertDataFrameToStringException model."""

    def __init__(self):
        super().__init__(CsvcubedExceptionMsges.FailedToConvertDataFrameToString.value)

    @classmethod
    def get_error_url(cls) -> str:
        return CsvcubedExceptionUrls.FailedToConvertDataFrameToString.value


class UnexpectedSparqlAskQueryResponseTypeException(CsvcubedException):
    """Class representing the UnexpectedSparqlAskQueryResponseTypeException model."""

    def __init__(self, query_name: str, response_type: type):
        super().__init__(
            CsvcubedExceptionMsges.UnexpectedSparqlAskQueryResponseType.value.format(
                query_name=query_name, response_type=response_type
            )
        )

    @classmethod
    def get_error_url(cls) -> str:
        return CsvcubedExceptionUrls.UnexpectedSparqlAskQueryResponseType.value


class UnexpectedSparqlAskQueryResultsException(CsvcubedException):
    """Class representing the UnexpectedSparqlAskQueryResultsException model."""

    def __init__(self, query_name: str, num_of_results: int):
        super().__init__(
            CsvcubedExceptionMsges.UnexpectedSparqlAskQueryResults.value.format(
                query_name=query_name, num_of_results=num_of_results
            )
        )

    @classmethod
    def get_error_url(cls) -> str:
        return CsvcubedExceptionUrls.UnexpectedSparqlAskQueryResults.value


class FeatureNotSupportedException(CsvcubedException):
    """Class representing the FeatureNotSupportedException model."""

    def __init__(self, explanation: str):
        super().__init__(
            CsvcubedExceptionMsges.FeatureNotSupported.value.format(
                explanation=explanation
            )
        )

    @classmethod
    def get_error_url(cls) -> str:
        return CsvcubedExceptionUrls.FeatureNotSupported.value


class ErrorProcessingDataFrameException(CsvcubedException):
    """Class representing the ErrorProcessingDataFrameException model."""

    def __init__(self, operation: str):
        super().__init__(
            CsvcubedExceptionMsges.ErrorProcessingDataFrame.value.format(
                operation=operation
            )
        )

    @classmethod
    def get_error_url(cls) -> str:
        return CsvcubedExceptionUrls.ErrorProcessingDataFrame.value


class UnsupportedColumnDefinitionException(CsvcubedException):
    """Class representing the UnsupportedColumnDefinitionException model."""

    def __init__(self, column_title: str):
        super().__init__(
            CsvcubedExceptionMsges.UnsupportedColumnDefinition.value.format(
                column_title=column_title
            )
        )

    @classmethod
    def get_error_url(cls) -> str:
        return CsvcubedExceptionUrls.UnsupportedColumnDefinition.value


class PrimaryKeyColumnTitleCannotBeNoneException(CsvcubedException):
    """Class representing the PrimaryKeyColumnTitleCannotBeNoneException model."""

    def __init__(self):
        super().__init__(CsvcubedExceptionMsges.PrimaryKeyColumnTitleCannotBeNone.value)

    @classmethod
    def get_error_url(cls) -> str:
        return CsvcubedExceptionUrls.PrimaryKeyColumnTitleCannotBeNone.value

class UnsupportedNumOfPrimaryKeyColNamesException(CsvcubedException):
    """Class representing the UnsupportedNumOfPrimaryKeyColNamesException model."""

    def __init__(self, num_of_primary_key_col_names: int, table_url:str):
        super().__init__(
            CsvcubedExceptionMsges.UnsupportedNumberOfPrimaryKeyColNames.value.format(
                num_of_primary_key_col_names=num_of_primary_key_col_names,
                table_url=table_url
            )
        )

    @classmethod
    def get_error_url(cls) -> str:
        return CsvcubedExceptionUrls.UnsupportedNumberOfPrimaryKeyColNames.value

class InvalidNumOfUnitColsForObsValColTitleException(CsvcubedException):
    """Class representing the InvalidNumOfUnitColsForObsValColTitleException model."""

    def __init__(self, obs_val_col_title: str, num_of_unit_cols:int):
        super().__init__(
            CsvcubedExceptionMsges.InvalidNumOfUnitColsForObsValColTitle.value.format(
                obs_val_col_title=obs_val_col_title,
                num_of_unit_cols=num_of_unit_cols
            )
        )

    @classmethod
    def get_error_url(cls) -> str:
        return CsvcubedExceptionUrls.InvalidNumOfUnitColsForObsValColTitle.value

class InvalidNumOfValUrlsForAboutUrlException(CsvcubedException):
    """Class representing the InvalidNumOfValUrlsForAboutUrlException model."""

    def __init__(self, about_url: str, num_of_value_urls: int):
        super().__init__(
            CsvcubedExceptionMsges.InvalidNumOfValUrlsForAboutUrl.value.format(
                about_url=about_url,
                num_of_value_urls=num_of_value_urls
            ) 
        )

    @classmethod
    def get_error_url(cls) -> str:
        return CsvcubedExceptionUrls.InvalidNumOfValUrlsForAboutUrl.value

class InvalidNumOfColsForColNameException(CsvcubedException):
    """Class representing the InvalidNumOfColsForColNameException model."""

    def __init__(self, column_name: str, num_of_cols: int):
        super().__init__(
            CsvcubedExceptionMsges.InvalidNumOfColsForColName.value.format(
                column_name=column_name,
                num_of_cols=num_of_cols
            ) 
        )

    @classmethod
    def get_error_url(cls) -> str:
        return CsvcubedExceptionUrls.InvalidNumOfColsForColName.value

class InvalidNumOfDSDComponentsForObsValColTitleException(CsvcubedException):
    """Class representing the InvalidNumOfDSDComponentsForObsValColTitleException model."""

    def __init__(self, obs_val_col_title: str, num_of_components: int):
        super().__init__(
            CsvcubedExceptionMsges.InvalidNumOfDSDComponentsForObsValColTitle.value.format(
                obs_val_col_title=obs_val_col_title,
                num_of_components=num_of_components
            ) 
        )

    @classmethod
    def get_error_url(cls) -> str:
        return CsvcubedExceptionUrls.InvalidNumOfDSDComponentsForObsValColTitle.value