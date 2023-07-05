import re
import shutil
import tempfile
from enum import Enum, unique
from pathlib import Path
from typing import Optional, Tuple, Union

import pytest
from click.testing import CliRunner

from globality_black.cli import main
from globality_black.constants import ALL_DONE_STRING, OH_NO_STRING
from globality_black.tests import run_and_check, show_diff
from globality_black.tests.fixtures import get_fixture_path


@unique
class FileCondition(Enum):
    NEEDS_GB = 0  # needs to be reformatted with globality-black
    NOTHING_TO_DO = 1
    HAS_ERRORS = 2


SINGLE_FILE_MAP = {
    FileCondition.NEEDS_GB: "blank_lines_input.txt",
    FileCondition.NOTHING_TO_DO: "blank_lines_output.txt",
    FileCondition.HAS_ERRORS: "file_with_errors.txt",
}


# the combination (False, True) is not possible since `diff` assumes `check` to be True
@pytest.mark.parametrize("check,diff", [(False, False), (True, False), (True, True)])
@pytest.mark.parametrize("verbose", (False, True))
@pytest.mark.parametrize("file_condition", tuple(FileCondition))
def test_cli_file(
    runner: CliRunner,
    check: bool,
    verbose: bool,
    diff: bool,
    file_condition: FileCondition,
):
    """
    We copy the input file to a temp directory, change the extension to .py and use
    globality-black
    Then compare output file, exit code and messages. We do this with and without check

    The file might have 3 possible conditions defined by FileCondition
    """

    file_to_test_cli = SINGLE_FILE_MAP[file_condition]
    has_errors = file_condition == FileCondition.HAS_ERRORS
    needs_gb = file_condition == FileCondition.NEEDS_GB

    fixture_input_path = get_fixture_path(file_to_test_cli)

    with tempfile.TemporaryDirectory() as temp_path:
        # copy file fixtures/*.txt -> temp_dir/*.py
        # we don't really need to change suffix to .py, but to make the test more realistic
        input_path = (Path(temp_path) / file_to_test_cli).with_suffix(".py")
        shutil.copy(str(fixture_input_path), str(input_path))
        result = run_globality_black(
            runner,
            input_path,
            dict(check=check, verbose=verbose, diff=diff),
        )
        output_message = result.stderr
        expected_exit_code = 1 if has_errors or check and needs_gb else 0
        assert result.exit_code == expected_exit_code

        if has_errors or check:
            expected_text = fixture_input_path.read_text()
        else:
            fixture_output_path = get_fixture_path(file_to_test_cli.replace("input", "output"))
            expected_text = fixture_output_path.read_text()

        output_text = input_path.read_text()  # formatted in-place
        _diff = show_diff(output_text, expected_text)  # noqa here to help debug
        assert output_text == expected_text

        per_file_string, final_count_string = get_strings(check, file_condition)

        if diff and needs_gb:
            # check the diff report is correct
            expected_diff_output_path = get_fixture_path(file_to_test_cli.replace("input", "diff"))
            diff_output = get_diff_report(output_message)
            expected_text = expected_diff_output_path.read_text()
            # we don't check the whole thing since `temp_path` is random
            _diff = show_diff(diff_output, expected_text)  # noqa here to help debug
            assert expected_text in diff_output

        emoji = OH_NO_STRING if expected_exit_code == 1 else ALL_DONE_STRING
        if verbose or needs_gb:
            pattern = f"{per_file_string} {input_path}.*{emoji}.*1 files {final_count_string}.*"
        else:
            pattern = f".*{emoji}.*1 files {final_count_string}.*"
        assert re.search(pattern, output_message, flags=re.DOTALL)


@pytest.mark.parametrize("check,diff", [(False, False), (True, False), (True, True)])
@pytest.mark.parametrize("verbose", (False, True))
@pytest.mark.parametrize("file_condition", tuple(FileCondition))
def test_cli_stdin(
    runner: CliRunner,
    check: bool,
    verbose: bool,
    diff: bool,
    file_condition: FileCondition,
):
    """
    Mirroring the test above, but passing the input via stdin instead of a file
    """

    file_to_test_cli = SINGLE_FILE_MAP[file_condition]
    has_errors = file_condition == FileCondition.HAS_ERRORS
    needs_gb = file_condition == FileCondition.NEEDS_GB

    fixture_input_path = get_fixture_path(file_to_test_cli)
    code = fixture_input_path.read_text()

    result = run_globality_black(
        runner,
        "-",
        dict(check=check, verbose=verbose, diff=diff),
        input=code,
    )
    output_code = result.stdout
    output_message = result.stderr

    expected_exit_code = 1 if has_errors or check and needs_gb else 0
    assert result.exit_code == expected_exit_code

    if has_errors or check:
        expected_text = ""
    else:
        fixture_output_path = get_fixture_path(file_to_test_cli.replace("input", "output"))
        expected_text = fixture_output_path.read_text()

    assert output_code == expected_text

    per_file_string, final_count_string = get_strings(check, file_condition)

    if diff and needs_gb:
        # check the diff report is correct
        expected_diff_output_path = get_fixture_path(file_to_test_cli.replace("input", "diff"))
        diff_output = get_diff_report(output_message)
        expected_text = expected_diff_output_path.read_text()
        # we don't check the whole thing since `temp_path` is random
        _diff = show_diff(diff_output, expected_text)  # noqa here to help debug
        assert expected_text in diff_output

    emoji = OH_NO_STRING if expected_exit_code == 1 else ALL_DONE_STRING
    if verbose or needs_gb:
        pattern = f"{per_file_string}.*{emoji}.*1 files {final_count_string}.*"
    else:
        pattern = f".*{emoji}.*1 files {final_count_string}.*"
    assert re.search(pattern, output_message, flags=re.DOTALL)


def run_globality_black(
    runner: CliRunner,
    path: Union[Path, str],
    kwargs: dict[str, bool],
    input: Optional[str] = None,
):
    args = [str(path)]

    for arg in ("check", "verbose", "diff"):
        if kwargs.get(arg, False):
            args.append(f"--{arg}")

    result = run_and_check(
        runner=runner,
        command_name="globality-black",
        command=main,
        args=args,
        input=input,
    )
    return result


def get_strings(check: bool, condition: FileCondition) -> Tuple[str, str]:
    if condition == FileCondition.HAS_ERRORS:
        per_file_string = "Failed to reformat"
        final_count_string = r"failed to parse \(black error\)"

    elif condition == FileCondition.NOTHING_TO_DO:
        per_file_string = "Nothing to do for"
        if check:
            final_count_string = "would be left unchanged"
        else:
            final_count_string = "unchanged"

    else:
        if check:
            per_file_string = "Would reformat"
            final_count_string = "would be reformatted"
        else:
            per_file_string = "Reformatted"
            final_count_string = "reformatted"

    return per_file_string, final_count_string


def get_diff_report(output: str) -> str:
    """
    Get only the diff component from the report
    """
    return "@@".join(output.split("@@")[1:])


@pytest.mark.parametrize("check", (False, True))
@pytest.mark.parametrize("error", (False, True))
@pytest.mark.parametrize("verbose", (False, True))
def test_cli_directory(runner: CliRunner, check: bool, error: bool, verbose: bool):
    """
    We copy 3 files (one of them already correctly formatted) to a directory. The first one will
    go to the root of the dir whereas the other 2 to a subdir.
    We check the files, messages and exit code after running globality-black with/without check

    When error is True, in addition to those 3 files, we copy a file with errors to the subdir
    """

    filenames = ["blank_lines_input.txt", "comprehensions_input.txt", "fmt_off_output.txt"]
    filenames = [Path(filename) for filename in filenames]  # type: ignore
    files_to_move_to_subdir = [False, True, True]
    file_conditions = [FileCondition.NEEDS_GB, FileCondition.NEEDS_GB, FileCondition.NOTHING_TO_DO]
    filenames_in_temp = []

    if error:
        filenames.append("file_with_errors.txt")
        files_to_move_to_subdir.append(True)
        file_conditions.append(FileCondition.HAS_ERRORS)

    with tempfile.TemporaryDirectory() as temp_path_str:
        # create subdir
        temp_path = Path(temp_path_str)
        (temp_path / "subdir").mkdir()

        # copy files fixtures/*.txt -> temp_dir/[subdir]/*.py
        for filename, to_subdir in zip(filenames, files_to_move_to_subdir):
            fixture_input_path = get_fixture_path(str(filename))
            destination_dir = temp_path / ("subdir" if to_subdir else "")
            filename_in_temp = (destination_dir / filename).with_suffix(".py")  # type: ignore
            shutil.copy(str(fixture_input_path), str(filename_in_temp))
            filenames_in_temp.append(filename_in_temp)

        result = run_globality_black(runner, temp_path, dict(check=check, verbose=verbose))
        expected_exit_code = 1 if check or error else 0
        assert result.exit_code == expected_exit_code

        for filename_in_temp, filename, to_subdir, condition in zip(
            filenames_in_temp, filenames, files_to_move_to_subdir, file_conditions
        ):
            # check files were reformatted / unchanged

            fixture_input_path = get_fixture_path(str(filename))
            input_text = filename_in_temp.read_text()
            if check or condition != FileCondition.NEEDS_GB:
                # should be unchanged
                expected_text = fixture_input_path.read_text()
            else:
                # should be reformatted
                expected_text = Path(str(fixture_input_path).replace("input", "output")).read_text()

            _diff = show_diff(input_text, expected_text)  # noqa here to help debug
            assert input_text == expected_text

            # check per file messages
            # since the reformatting is run in parallel, we cannot guarantee the order of the
            # messages. So we just check the message is somewhere **in** the output
            pre_string, _ = get_strings(check, condition)
            # only check if verbose=True or something needed for this file
            if verbose or pre_string != "Nothing to do for":
                assert f"{pre_string} {filename_in_temp}" in result.stderr

        # check for the end of the message

        emojis = OH_NO_STRING if expected_exit_code == 1 else ALL_DONE_STRING

        string_changed = "would be reformatted" if check else "reformatted"
        string_unchanged = "would be left unchanged" if check else "unchanged"

        final_string = f"\n2 files {string_changed}\n1 files {string_unchanged}\n"
        if error:
            final_string = "\n1 files failed to parse (black error)" + final_string
        final_string = emojis + final_string

        assert result.stderr.endswith(final_string)
