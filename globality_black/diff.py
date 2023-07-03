from pathlib import Path
from typing import Union

from black import color_diff, diff


def text_diff(
    input_code: str,
    output_code: str,
    input_path: Union[Path, str] = "",
) -> str:
    """
    Report the differences that globality black will make to input_path file
    in a git-like format leveraging code already in black.
    """

    diff_contents = diff(a=input_code, b=output_code, a_name="", b_name=str(input_path))
    diff_contents = color_diff(diff_contents)
    return diff_contents
