from pathlib import Path
from pkg_resources import resource_filename


def get_fixture_path(fixture_name: str) -> Path:
    # TODO: grabbed from web-annotation-extractor. Should this be in some generic library?
    return Path(
        resource_filename(__name__, fixture_name),
    )
