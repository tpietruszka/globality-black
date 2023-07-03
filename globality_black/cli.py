"""Console script for globality_black."""
import multiprocessing as mp
import sys
from functools import partial
from pathlib import Path
from typing import Union

import click

from globality_black.black_handler import get_black_mode
from globality_black.constants import (
    ALL_DONE_STRING,
    NUM_FILES_TO_ENABLE_PARALLELIZATION,
    OH_NO_STRING,
)
from globality_black.diff import text_diff
from globality_black.reformat_text import BlackError, reformat_text


@click.command()
@click.option("--check/--no-check", is_flag=True)
@click.option("--verbose/--no-verbose", is_flag=True)
@click.option(
    "--code/--no-code",
    type=bool,
    help="Format the code passed in as a string.",
    default=False,
)
@click.option("--diff/--no-diff", is_flag=True)
# characters \b needed to avoid click reformatting
# see https://click.palletsprojects.com/en/7.x/documentation/#preventing-rewrapping
@click.argument(
    "src",
    type=click.Path(exists=True, file_okay=True, dir_okay=True, readable=True, allow_dash=True),
    required=False,
    is_eager=True,
)
def main(src, check: bool, diff: bool, code: bool, verbose: bool):
    """
    Run globality-black for a given path

    \b
    * path:
        If path is a directory, apply to all .py files in any subdirectory
        Otherwise, apply just to the given filename.

    \b
    * check:
        If --check is passed, do not modify the files and return:
            - exit code 1: if any file needs to be reformatted (or fails when applying black)
            - exit code 0: otherwise
        \b
        If --check not passed (or --no-check is passed), attempt to reformat all paths returning
            - exit code 1: if any file fails
            - exit code 0: otherwise
        \b
        Note that when not passing --check, all files not failing will be correctly reformatted
        (i.e. globality-black is independently applied per-file)

    \b
    * verbose:
        If --verbose not passed (or --no-verbose), only files with errors or to be modified are
        shown

    \b
    * diff:
        If --diff, do not modify the files and display the changes induced by reformatting

    """
    if code:
        # this bit is used by the `External formatters` VScode extension
        input_code = sys.stdin.read()
        output_code, output_msg, *_ = process_src(input_code)
        # not sure why but VScode adds a newline at the end of the output
        assert isinstance(output_code, str)
        output_code = output_code[:-1]
        # use stderr for the output msg, to avoid writing into the file
        assert isinstance(output_msg, str)
        click.echo(output_msg, file=sys.stderr)
        click.echo(output_code, file=sys.stdout)
        return
    if src is None:
        raise ValueError("src should be passed if not using --code")

    path = Path(src)
    assert path.exists(), f"Path {path} does not exist"

    exit_code = 0
    if diff:
        check = True
    if path.is_dir():
        paths = list(path.glob("**/*.py"))
    else:
        paths = [path]

    reformatted_count, failed_count = 0, 0
    process_path_with_check = partial(process_src, check_only_mode=check, diff_mode=diff)

    parallelize = len(paths) > NUM_FILES_TO_ENABLE_PARALLELIZATION
    if parallelize:
        with mp.Pool(mp.cpu_count() - 1) as pool:
            map_result = pool.map(process_path_with_check, paths)
    else:
        # Do not parallelize if just a few files
        map_result = list(map(process_path_with_check, paths))

    for is_modified, is_failed, message in map_result:  # type: ignore
        if verbose or is_modified or is_failed:
            click.echo(message)
        reformatted_count += is_modified
        failed_count += is_failed

    unchanged_count = len(paths) - reformatted_count - failed_count

    # add a separator line
    click.echo("-" * len(OH_NO_STRING))

    # if we are just checking and at least one file needs to be reformatted OR some file failed
    if (check and reformatted_count > 0) or failed_count > 0:
        click.echo(OH_NO_STRING)
        exit_code = 1
        if failed_count > 0:
            click.echo(f"{failed_count} files failed to parse (black error)")
    else:
        click.echo(ALL_DONE_STRING)

    if check:
        if reformatted_count > 0:
            click.echo(f"{reformatted_count} files would be reformatted")
        if unchanged_count > 0:
            click.echo(f"{unchanged_count} files would be left unchanged")
    else:
        if reformatted_count > 0:
            click.echo(f"{reformatted_count} files reformatted")
        if unchanged_count > 0:
            click.echo(f"{unchanged_count} files unchanged")

    sys.exit(exit_code)


def process_src(
    src: Union[Path, str],
    check_only_mode: bool = False,
    diff_mode: bool = False,
) -> Union[tuple[str, str], tuple[bool, bool, str]]:
    """
    For each path compute `is_modified`, `is_failed`, and `message` to be used in main
    """

    is_modified = False
    file_mode = isinstance(src, Path)
    if file_mode:
        input_code = src.read_text()  # type: ignore
        black_mode = get_black_mode(src)
        path = src
    else:
        input_code = src
        black_mode = get_black_mode(".")

    path_str = f" {path}" if file_mode else ""
    diff_output = ""

    try:
        output_code = reformat_text(input_code, black_mode)
    except BlackError as e:
        return False, True, f"Failed to reformat{path_str}. {e}"

    if input_code != output_code:
        is_modified = True

    if check_only_mode and is_modified:
        if diff_mode:
            diff_output = text_diff(input_code, output_code, path)
            diff_path_str = f" for {path}" if file_mode else ""
            diff_output = f"\nDiff{diff_path_str} \n" + diff_output
        initial_str = "Would reformat"
    elif not check_only_mode and is_modified:
        initial_str = "Reformatted"
    else:
        initial_str = "Nothing to do for"

    if not check_only_mode and file_mode:
        path.write_text(output_code)  # type: ignore

    path_str = f" {path}" if file_mode else ""
    if diff_mode:
        # if diff we add the diff report to the reformat message

        output_msg = diff_output + "\n" + f"{initial_str}{path_str}"
    else:
        output_msg = f"{initial_str}{path_str}"

    if file_mode:
        return is_modified, False, output_msg
    return output_code, output_msg


if __name__ == "__main__":
    sys.exit(main())  # type: ignore # pragma: no cover
