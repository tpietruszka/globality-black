import pytest

from globality_black.black_handler import get_black_mode
from globality_black.reformat_text import reformat_text
from globality_black.tests import show_diff
from globality_black.tests.fixtures import get_fixture_path


@pytest.mark.parametrize(
    "feature",
    [
        "blank_lines",
        "fmt_off",
        "comprehensions",
        "dotted_chains",
        "tuples",
    ],
)
def test_reformat_text(feature):
    path = get_fixture_path(f"{feature}_input.txt")
    expected_output = get_fixture_path(f"{feature}_output.txt").read_text()

    black_mode = get_black_mode(path)
    output = reformat_text(path.read_text(), black_mode)

    diff = show_diff(output, expected_output)  # noqa here to help debug
    if expected_output != output:
        print(diff)  # noqa
    assert expected_output == output
