"""
Version
---

Utility to return csvcubed version specific infomation.
"""
from csvcubed.__init__ import __version__


def get_csvcubed_version_uri():
    versionNumber = f"https://github.com/GSS-Cogs/csvcubed/releases/tag/v{__version__}"
    return versionNumber
