"""Main Script for m4b-util."""
from . import split


# We don't test coverage for this, since we don't test it directly.
# We just make it simple enough that we can trust it works.
if __name__ == "__main__":  # pragma: no cover
    split.run()  # pragma: no cover
