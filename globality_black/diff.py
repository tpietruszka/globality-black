import tempfile
from pathlib import Path

import pexpect


def git_diff(input_path: Path, output_code: str) -> str:
    """
    Use git diff to report the differences that globality black
    will make to input_path file
    pexpect is used over subprocess because of better color handling
    """

    with tempfile.NamedTemporaryFile(mode="w+t") as temp_file:
        temp_file.writelines(output_code)
        temp_file.seek(0)
        output = pexpect.run(f"git --no-pager diff --no-index {input_path} {temp_file.name}")
        return output.decode()
