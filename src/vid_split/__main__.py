"""Main Script for m4b-util."""
import argparse
import sys

from rich import print

from . import split
from .__version__ import version


def _print_version():
    """Print the current version, then exit."""
    print(f"[green]vid-split[/], Version '{version}'")
    return 0


# We don't test coverage for this, since we don't test it directly.
# We just make it simple enough that we can trust it works.
if __name__ == "__main__":  # pragma: no cover
    split.run()  # pragma: no cover
