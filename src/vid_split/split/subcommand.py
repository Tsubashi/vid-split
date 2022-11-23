import argparse
from pathlib import Path
import sys

from rich import print

from .SilenceFinder import SilenceFinder
from .Splitter import Splitter
from ..__version__ import version


def _parse_args():
    parser = argparse.ArgumentParser(
        prog="vid-split",
        description='Split media into segments.'
    )
    parser.add_argument('input_file', nargs="?", help='Input file (Required)')

    parser.add_argument('-b', "--buffer", type=float, default=0.,
                        help='Number of second to include before and after each segment.')
    parser.add_argument('-e', "--end-time", type=float, help='End time (seconds)')
    parser.add_argument('-m', "--minimum_segment_time", type=float, default=0.25,
                        help='Smallest segment size to consider, in seconds.')
    parser.add_argument('-o', "--output-dir", type=str, help="Directory to place output.")
    parser.add_argument('-p', '--output-pattern', type=str, default="segment_{i:04d}.mp4",
                        help="Output filename pattern (e.g. `segment_{i:04d}.mp4`), use '{i}' for sequence and "
                             "'{title}' for chapter title.")
    parser.add_argument('-s', "--start-time", type=float, help='Start time (seconds)')
    parser.add_argument('-V', "--version", action="store_true", help='Show version and exit.')

    silence_options = parser.add_argument_group('silence detection options')
    silence_options.add_argument("--silence-threshold", default=-35, type=int, help='Silence threshold (in dB)')
    silence_options.add_argument("--silence-duration", default=0.25, type=float, help='Silence duration')

    args = parser.parse_args()
    if args.version:
        print(f"[green]vid-split[/], Version '{version}'")
        exit(0)

    if not args.input_file:
        parser.error("Input file is required.")

    return args


def run():
    """Split a file into pieces, based on silence."""
    args = _parse_args()
    input_path = Path(args.input_file)

    # Step 1: Look for where the splits should be.
    segment_list = SilenceFinder(
        input_path=input_path,
        start_time=args.start_time,
        end_time=args.end_time,
        silence_duration=args.silence_duration,
        silence_threshold=args.silence_threshold,
    ).find()

    if not segment_list:
        print("[bold red]Error:[/] No segments found.")
        exit(1)

    # Step 2: Filter out too-small segments
    # Use .copy() so that we can modify the original without throwing off the iterator
    for segment in segment_list.copy():
        if segment.end_time - segment.start_time < args.minimum_segment_time:
            segment_list.remove(segment)
    if len(segment_list) == 0:
        print("[bold red]Error:[/] Not enough segments found.")
        exit(1)

    # Step 3: Split the original file
    print(f"[yellow]Info:[/] Found [yellow]{len(segment_list)}[/] segments")
    if args.output_dir:
        output_path = Path(args.output_dir)
    else:
        output_path = Path()
    Splitter(
        buffer=args.buffer,
        input_path=input_path,
        output_dir_path=output_path,
        output_pattern=args.output_pattern,
        segment_list=segment_list
    ).split()


