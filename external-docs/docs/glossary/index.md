# Glossary

## [Aggregate](https://ec.europa.eu/eurostat/statistics-explained/index.php?title=Beginners:Statistical_concept_-_Aggregate)

An aggregate is formed when multiple numbers are gathered for statistical purposes and are expressed as one number. This could be in the form of a total or an average.

## [Attribute](https://www.w3.org/TR/vocab-data-cube/#cubes-model)

 An attribute component allows us to qualify and interpret an observed value. They enable specification of the units of measure and metadata such as the status of the observation (e.g. estimated, provisional).

## [Code List](https://sdmx.org/wp-content/uploads/SDMX_Glossary_version_2_1-Final-2.docx)

Predefined set of codified concepts which represent the distinct values that a dimension can hold.

## [CSV-W](https://www.w3.org/TR/tabular-data-primer/)

Comma Separated Values on the Web – a standardised format to express metadata describing the contents of CSV files. For more information, see the [W3C project page](https://www.w3.org/TR/tabular-data-primer/) on this topic.

## Dense Data

A dense data set is one where the majority of dimension combinations have observed values recorded. Compare to [sparse](#sparse-data) data sets.

## [Dimension](https://www.w3.org/TR/vocab-data-cube/#cubes-model)

Dimension components identify the subset of a population which has been observed. A set of values for all the dimension components is sufficient to identify a single observation. Examples of dimensions include the time to which the observation applies, or the geographic region that the observation covers.

## Literal

Basic values such as strings, dates, booleans, and numbers that can only be used in the object position of an RDF triple.
Literals are values which can take the form of strings, numbers, dates and booleans. See the CSV-W [built-in data types](https://www.w3.org/TR/2015/REC-tabular-metadata-20151217/#h-built-in-datatypes).

## [Measure](https://www.w3.org/TR/vocab-data-cube/#cubes-model)

A measure defines the population characteristic or phenomenon which has been observed and recorded.

Examples:

* `Birthrate`
* `GDP Per Capita`
* `Distance of Daily Commute`

## [Observation / Observed Value](https://www.w3.org/TR/vocab-data-cube/#cubes-model)

A value which has been observed. It is to be interpreted with its corresponding unit and measure values as well as its dimension values. The dimension values define the sub set of the population that the observed value applies to.

## [Pivoted Shape](../guides/shape-data/pivoted-shape.md)

One of two data shapes that are accepted by csvcubed. The pivoted shape permits multiple observation value columns to be defined, which minimises redundancy in your data set. Compare to the [standard shape](#standard-shape).

## Population Characteristic

A property of a population which can be measured or observed. For example, height in a population of people or income in a population of households.

## Resource

Resources are objects or concepts that exist in the real world that can be expressed in a machine-readable format by
converting them to [URIs](#uniform-resource-identifier). Resources form the basis of the Resource Description
Framework (RDF), and are fundamental to the concept of [linked data](https://www.w3.org/TR/vocab-data-cube/#intro-rdf).

## [Semantic Web](https://www.w3.org/RDF/Metalog/docs/sw-easy)

An extension to the world wide web in which information is given structured meaning using vocabularies such as [Simple Knowledge Organisation System (SKOS)](https://www.w3.org/2004/02/skos/intro) and the [RDF Data Cube vocabulary](https://www.w3.org/TR/vocab-data-cube/). The csvcubed tools help you build statistics which fit into the semantic web of linked data.

## Sparse Data

A sparse data set is one where there are a large number of possible combinations of dimension values, but very few of them have observed values recorded. Compare to [dense](#dense-data) data sets.

## [Standard Shape](../guides/shape-data/standard-shape.md)

One of two data shapes that are accepted by csvcubed. The standard shape requires that observation values are stored in a single column and are further identified using the measure and unit columns. Compare to the [pivoted shape](#pivoted-shape).

## Tidy Data

A standard data shape/layout designed to ensure interoperability between data tools. A tidy data set is arranged such that each dimension is a single column and each observation a single row. For more information, see Hadley Wickham's [paper on this topic](https://www.jstatsoft.org/index.php/jss/article/view/v059i10/v59i10.pdf).

## [Unit](https://sdmx.org/wp-content/uploads/SDMX_Glossary_version_2_1-Final-2.docx)

A quantity or increment by which something is counted or described, such as kg, mm, °C, °F, monetary units such as Euro or US dollar, simple number counts or index numbers.

## [Uniform Resource Identifier](https://www.w3.org/TR/vocab-data-cube/#intro-rdf)

Uniform Resource Identifiers (URIs) are identifiers which distinguish [resources](#resource) from one another. Note that a URL (Uniform Resource Locator) is a type of URI.
Examples:

* `http://some-uri`
* `http://base-uri/concept-scheme/this-concept-scheme-name`
* `https://onsdigital.github.io/csvcubed-docs/external/glossary/`
* `ftp://example.example/example/example.txt`
* `mailto:example@example.example`

For more information regarding the use of URIs on the semantic web, [see this W3C resource](https://www.w3.org/TR/cooluris/)
