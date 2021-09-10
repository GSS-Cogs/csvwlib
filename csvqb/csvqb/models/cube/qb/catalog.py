"""
Catalog Metadata (DCAT)
-----------------------
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from sharedmodels.rdf import dcat

from csvqb.models.cube.catalog import CatalogMetadataBase
from csvqb.models.uriidentifiable import UriIdentifiable
from csvqb.utils.validators.uri import validate_uri


@dataclass
class CatalogMetadata(CatalogMetadataBase, UriIdentifiable):
    identifier: Optional[str] = None
    summary: Optional[str] = field(default=None, repr=False)
    description: Optional[str] = field(default=None, repr=False)
    creator_uri: Optional[str] = field(default=None, repr=False)
    publisher_uri: Optional[str] = field(default=None, repr=False)
    landing_page_uri: Optional[str] = field(default=None, repr=False)
    theme_uris: list[str] = field(default_factory=list, repr=False)
    keywords: list[str] = field(default_factory=list, repr=False)
    dataset_issued: Optional[datetime] = field(default=None, repr=False)
    dataset_modified: Optional[datetime] = field(default=None, repr=False)
    license_uri: Optional[str] = field(default=None, repr=False)
    public_contact_point_uri: Optional[str] = field(default=None, repr=False)
    uri_safe_identifier_override: Optional[str] = field(default=None, repr=False)

    _creator_uri_validator = validate_uri("creator_uri", is_optional=True)
    _publisher_uri_validator = validate_uri("publisher_uri", is_optional=True)
    _landing_page_uri_validator = validate_uri("landing_page_uri", is_optional=True)
    _license_uri_validator = validate_uri("license_uri", is_optional=True)
    _public_contact_point_uri_validator = validate_uri(
        "public_contact_point_uri", is_optional=True
    )

    def get_issued(self) -> Optional[datetime]:
        return self.dataset_issued

    def get_description(self) -> Optional[str]:
        return self.description

    def get_identifier(self) -> str:
        return self.identifier or self.title

    def configure_dcat_dataset(self, dataset: dcat.Dataset) -> None:
        dt_now = datetime.now()
        dt_issued = self.dataset_issued or dt_now

        dataset.label = dataset.title = self.title
        dataset.issued = dt_issued
        dataset.modified = self.dataset_modified or dt_issued
        dataset.comment = self.summary
        dataset.description = self.description
        dataset.license = self.license_uri
        dataset.creator = self.creator_uri
        dataset.publisher = self.publisher_uri
        dataset.landing_page = self.landing_page_uri
        dataset.themes = set(self.theme_uris)
        dataset.keywords = set(self.keywords)
        dataset.contact_point = self.public_contact_point_uri
        dataset.identifier = self.get_identifier()
