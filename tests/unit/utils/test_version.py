from csvcubed.utils.version import get_csvcubed_version_uri


def test_get_csvcubed_version():
    # The version number returned can have .dev0 appended which doesn't technically exist
    # as a valid release url.
    # So we check the prefix to this which should exist or if no .dev0 the whole URI is
    # checked.

    version_number = get_csvcubed_version_uri()

    assert (
        "https://github.com/ONSdigital/csvcubed/releases/tag/v" in version_number
    ), f"{version_number} does not appear to be a release tag URL"
