from typing import Annotated, Union, Set
from abc import ABC
from rdflib import Literal, URIRef, RDFS


import sharedmodels.rdf.rdf as rdf
import sharedmodels.rdf.rdfs as rdfs
import sharedmodels.rdf.skos as skos
from sharedmodels.rdf.rdfresource import RdfResource, map_entity_to_uri
from sharedmodels.rdf.triple import Triple, PropertyStatus
from sharedmodels.rdf.namespaces import QB


class ComponentProperty(rdf.PropertyWithMetadata):
    """Component property (abstract) - Abstract super-property of all properties representing dimensions, attributes
    or measures"""
    concept: Annotated[skos.Concept, Triple(QB.concept, PropertyStatus.recommended, map_entity_to_uri)]
    """concept - gives the concept which is being measured or indicated by a ComponentProperty"""

    def __init__(self, uri: str):
        rdf.Property.__init__(self, uri)
        self.rdf_types.add(QB.ComponentProperty)


class MeasureProperty(ComponentProperty):
    """Measure property - The class of components which represent the measured value of the phenomenon being observed"""

    range: Annotated[str, Triple(RDFS.range, PropertyStatus.mandatory, URIRef)]
    """range - the `rdfs:range` associated with this measure property. i.e. the value types the measured values can 
    range over."""

    def __init__(self, uri: str):
        ComponentProperty.__init__(self, uri)
        self.rdf_types.add(QB.MeasureProperty)


class CodedProperty(ComponentProperty):
    """Coded property - Superclass of all coded ComponentProperties"""
    code_list: Annotated[Union[skos.ConceptScheme, skos.Collection, "HierarchicalCodeList"],
                         Triple(QB.codeList, PropertyStatus.recommended, map_entity_to_uri)]
    """code list - gives the code list associated with a CodedProperty"""

    def __init__(self, uri: str):
        ComponentProperty.__init__(self, uri)
        self.rdf_types.add(QB.CodedProperty)


class DimensionProperty(CodedProperty):
    """Dimension property - The class of components which represent the dimensions of the cube"""

    range: Annotated[str, Triple(RDFS.range, PropertyStatus.mandatory, URIRef)]
    """range - the `rdfs:range` associated with this measure property. i.e. the value types the measured values can 
    range over."""

    def __init__(self, uri: str):
        CodedProperty.__init__(self, uri)
        ComponentProperty.__init__(self, uri)
        self.rdf_types.add(QB.DimensionProperty)


class HierarchicalCodeList(RdfResource):
    """Hierarchical Code List - Represents a generalized hierarchy of concepts which can be used for coding. The
    hierarchy is defined by one or more roots together with a property which relates concepts in the hierarchy to
    thier child concept .  The same concepts may be members of multiple hierarchies provided that different
    qb:parentChildProperty values are used for each hierarchy."""
    parentChildProperty: Annotated[rdf.Property, Triple(QB.parentChildProperty, PropertyStatus.recommended,
                                                        map_entity_to_uri)]
    """parent-child property - Specifies a property which relates a parent concept in the hierarchy to a child 
    concept."""

    def __init__(self, uri: str):
        RdfResource.__init__(self, uri)
        self.rdf_types.add(QB.HierarchicalCodeList)


class Attachable(RdfResource, ABC):
    """Attachable (abstract) - Abstract superclass for everything that can have attributes and dimensions"""

    def __init__(self, uri: str):
        RdfResource.__init__(self, uri)
        self.rdf_types.add(QB.Attachable)


class ComponentSet(RdfResource, ABC):
    """Component set - Abstract class of things which reference one or more ComponentProperties"""
    componentProperties: Annotated[Set[ComponentProperty], Triple(QB.componentProperties,
                                                                  PropertyStatus.recommended, map_entity_to_uri)]
    """component - indicates a ComponentProperty (i.e. attribute/dimension) expected on a DataSet, or a dimension 
    fixed in a SliceKey"""

    def __init__(self, uri: str):
        RdfResource.__init__(self, uri)
        self.rdf_types.add(QB.ComponentSet)
        self.componentProperties = set()


class AttributeProperty(ComponentProperty):
    """Attribute property - The class of components which represent attributes of observations in the cube,
    e.g. unit of measurement"""

    def __init__(self, uri: str):
        ComponentProperty.__init__(self, uri)
        self.rdf_types.add(QB.AttributeProperty)


class ComponentSpecification(ComponentSet, ABC):
    """Component specification - Used to define properties of a component (attribute, dimension etc) which are
    specific to its usage in a DSD."""
    order: Annotated[int, Triple(QB.order, PropertyStatus.recommended, Literal)]
    """order - indicates a priority order for the components of sets with this structure, used to guide presentations 
    - lower order numbers come before higher numbers, un-numbered components come last"""

    def __init__(self, uri: str):
        ComponentSet.__init__(self, uri)
        self.rdf_types.add(QB.ComponentSpecification)


class AttributeComponentSpecification(ComponentSpecification):
    """See https://www.w3.org/TR/vocab-data-cube/#dsd-dsd - manually defined, not normative Qb spec."""

    componentAttachment: Annotated[rdfs.Class, Triple(QB.componentAttachment, PropertyStatus.recommended,
                                                      map_entity_to_uri)]
    """component attachment - Indicates the level at which the component property should be attached, this might an 
    qb:DataSet, qb:Slice or qb:Observation, or a qb:MeasureProperty."""

    componentRequired: Annotated[bool, Triple(QB.componentRequired, PropertyStatus.recommended, Literal)]
    """component required - Indicates whether a component property is required (true) or optional (false) in the 
    context of a DSD. Only applicable to components correspond to an attribute. Defaults to false (optional)."""

    attribute: Annotated[AttributeProperty, Triple(QB.attribute, PropertyStatus.recommended,
                                                   map_entity_to_uri)]
    """See https://www.w3.org/TR/vocab-data-cube/#dsd-dsd"""

    def __init__(self, uri: str):
        ComponentSpecification.__init__(self, uri)


class DimensionComponentSpecification(ComponentSpecification):
    """See https://www.w3.org/TR/vocab-data-cube/#dsd-dsd - manually defined, not normative Qb spec."""

    dimension: Annotated[DimensionProperty, Triple(QB.dimension, PropertyStatus.recommended,
                                                   map_entity_to_uri)]
    """See https://www.w3.org/TR/vocab-data-cube/#dsd-dsd"""

    def __init__(self, uri: str):
        ComponentSpecification.__init__(self, uri)


class MeasureComponentSpecification(ComponentSpecification):
    """See https://www.w3.org/TR/vocab-data-cube/#dsd-dsd - manually defined, not normative Qb spec."""

    dimension: Annotated[MeasureProperty, Triple(QB.measure, PropertyStatus.recommended,
                                                 map_entity_to_uri)]
    """See https://www.w3.org/TR/vocab-data-cube/#dsd-dsd"""

    def __init__(self, uri: str):
        ComponentSpecification.__init__(self, uri)


class SliceKey(ComponentSet):
    """Slice key - Denotes a subset of the component properties of a DataSet which are fixed in the corresponding
    slices"""

    def __init__(self, uri: str):
        ComponentSet.__init__(self, uri)
        self.rdf_types.add(QB.SliceKey)


class DataStructureDefinition(ComponentSet):
    """Data structure definition - Defines the structure of a DataSet or slice"""
    components: Annotated[Set[ComponentSpecification],
                          Triple(QB.component, PropertyStatus.recommended, map_entity_to_uri)]
    """component specification - indicates a component specification which is included in the structure of the 
    dataset"""

    sliceKey: Annotated[SliceKey, Triple(QB.sliceKey, PropertyStatus.recommended, map_entity_to_uri)]
    """slice key - indicates a slice key which is used for slices in this dataset"""

    def __init__(self, uri: str):
        ComponentSet.__init__(self, uri)
        self.rdf_types.add(QB.DataStructureDefinition)
        self.components = set()


class Observation(Attachable):
    """Observation - A single observation in the cube, may have one or more associated measured values"""
    dataSet: Annotated["DataSet", Triple(QB.dataSet, PropertyStatus.recommended, map_entity_to_uri)]
    """data set - indicates the data set of which this observation is a part"""

    def __init__(self, uri: str):
        Attachable.__init__(self, uri)
        self.rdf_types.add(QB.Observation)


class DataSet(Attachable):
    """Data set - Represents a collection of observations, possibly organized into various slices, conforming to some
    common dimensional structure."""
    slices: Annotated[Set["Slice"], Triple(QB.slice, PropertyStatus.recommended, map_entity_to_uri)]
    """slice - Indicates a subset of a DataSet defined by fixing a subset of the dimensional values"""

    structure: Annotated["DataStructureDefinition", Triple(QB.structure, PropertyStatus.recommended,
                                                           map_entity_to_uri)]
    """structure - indicates the structure to which this data set conforms"""

    def __init__(self, uri: str):
        Attachable.__init__(self, uri)
        self.rdf_types.add(QB.DataSet)
        self.slices = set()


class ObservationGroup(RdfResource):
    """Observation Group - A, possibly arbitrary, group of observations."""
    observations: Annotated[Set["Observation"], Triple(QB.observation, PropertyStatus.recommended,
                                                       map_entity_to_uri)]
    """observation - indicates a observation contained within this slice of the data set"""

    def __init__(self, uri: str):
        RdfResource.__init__(self, uri)
        self.rdf_types.add(QB.ObservationGroup)
        self.observations = set()


class Slice(Attachable, ObservationGroup):
    """Slice - Denotes a subset of a DataSet defined by fixing a subset of the dimensional values, component
    properties on the Slice"""
    sliceStructure: Annotated["SliceKey", Triple(QB.sliceStructure, PropertyStatus.recommended,
                                                 map_entity_to_uri)]
    """slice structure - indicates the sub-key corresponding to this slice"""

    def __init__(self, uri: str):
        Attachable.__init__(self, uri)
        ObservationGroup.__init__(self, uri)
        self.rdf_types.add(QB.Slice)
