"""Test the split subcommand."""
from contextlib import contextmanager
import os
from pathlib import Path
from unittest import mock

import pytest

from vid_split import split
from vid_split.helpers import ffprobe
import testhelpers


@contextmanager
def change_cwd(new_path):
    """Change to a new directory, then change back when finished."""
    owd = Path.cwd()  # Original Working Directory
    os.chdir(new_path)
    try:
        yield
    finally:
        os.chdir(owd)


def _run_split_cmd(arg_list):
    """Patch the runtime arguments, then run the split command."""
    argv_patch = ["vid-split"]
    argv_patch.extend(arg_list)

    with mock.patch("sys.argv", argv_patch):
        split.run()


def test_split_silence(tmp_path, silences_file_path):
    """Split a file on silence, default settings."""
    output_path = tmp_path / "output"
    output_path.mkdir()
    expected_files = [
        "segment_0000.mp4",
        "segment_0001.mp4",
        "segment_0002.mp4",
        "segment_0003.mp4",
    ]
    with change_cwd(output_path):
        _run_split_cmd([str(silences_file_path), "--silence-duration", "1.0"])
        testhelpers.check_output_folder(output_path, expected_files)


def test_split_audio_start_end_times(tmp_path, silences_file_path):
    """Split a file, with start and end times specified."""
    output_path = tmp_path / "output"
    _run_split_cmd([
            str(silences_file_path),
            "-o", str(output_path),
            "-s", "1.75",
            "-e", "5.03"
        ])
    testhelpers.check_output_folder(output_path)


def test_split_audio_fail(tmp_path, capsys):
    """Exit with non-zero code when asked to process a non-audio file."""
    fake_file_path = tmp_path / "not-a-real-file.m4a"
    open(fake_file_path, 'a').close()
    with pytest.raises(SystemExit) as e:
        _run_split_cmd([str(fake_file_path), "-o", str(tmp_path)])
    assert (e.value.code == 1)
    output = capsys.readouterr()
    assert "Could not determine segment times." in output.out


def test_split_audio_duration(tmp_path, silences_file_path):
    """Adjust silence duration limits."""
    output_path = tmp_path / "output"
    cmd = [
        str(silences_file_path),
        "-o", str(output_path),
        "--silence-duration", "1.5"
    ]
    expected_files = (
        "segment_0000.mp4",
        "segment_0001.mp4",
        "segment_0002.mp4",
        "segment_0003.mp4",
    )
    _run_split_cmd(cmd)
    testhelpers.check_output_folder(output_path, expected_files)


def test_split_audio_threshold_lower(tmp_path, variable_volume_segments_file_path, capsys):
    """Adjust silence threshold limits to a threshold lower than any noise in the file."""
    output_path = tmp_path / "output"
    cmd = [
        str(variable_volume_segments_file_path),
        "-o", str(output_path),
        "--silence-threshold", "-45",
        "--silence-duration", "1.5"
    ]
    with pytest.raises(SystemExit) as e:
        _run_split_cmd(cmd)
    assert (e.value.code == 1)
    output = capsys.readouterr()
    assert "No segments found." in output.out


def test_split_audio_threshold_higher(tmp_path, variable_volume_segments_file_path, capsys):
    """Adjust silence threshold limits to a threshold higher than any noise in the file."""
    output_path = tmp_path / "output"
    cmd = [
        str(variable_volume_segments_file_path),
        "-o", str(output_path),
        "--silence-threshold", "-5",
        "--silence-duration", "1.5"
    ]
    with pytest.raises(SystemExit) as e:
        _run_split_cmd(cmd)
    assert (e.value.code == 1)
    output = capsys.readouterr()
    assert "Not enough segments found." in output.out


def test_split_audio_threshold(tmp_path, variable_volume_segments_file_path):
    """Adjust silence threshold limits to a threshold right between the two volume levels in the file."""
    output_path = tmp_path / "output"
    cmd = [
        str(variable_volume_segments_file_path),
        "-o", str(output_path),
        "--silence-threshold", "-20",
        "--silence-duration", "1.5"
    ]
    expected_files = (
        "segment_0000.mp4",
        "segment_0001.mp4",
        "segment_0002.mp4",
        "segment_0003.mp4",
    )
    _run_split_cmd(cmd)
    testhelpers.check_output_folder(output_path, expected_files)


def test_split_audio_segment_pattern(tmp_path, silences_file_path):
    """Specify a non-default segment pattern."""
    output_path = tmp_path / "output"
    cmd = [
        str(silences_file_path),
        "-o", str(output_path),
        "--silence-duration", "1.5",
        "-p", "chunk_{:02d}.mp4",
    ]
    # Make sure the files we expect are there
    expected_files = (
        "chunk_00.mp4",
        "chunk_01.mp4",
        "chunk_02.mp4",
        "chunk_03.mp4",
    )
    _run_split_cmd(cmd)
    testhelpers.check_output_folder(output_path, expected_files)


def test_version(capsys):
    with pytest.raises(SystemExit) as e:
        _run_split_cmd(["--version"])
    assert e.value.code == 0
    output = capsys.readouterr()
    assert "vid-split" in output.out


def test_no_args(capsys):
    with pytest.raises(SystemExit) as e:
        _run_split_cmd([])
    assert e.value.code == 2
    output = capsys.readouterr()
    assert "Input file is required" in output.err

