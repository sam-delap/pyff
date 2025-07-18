"""Helper Functions related to handling file caching"""

from io import TextIOWrapper
from pathlib import Path


def load_file_cache(file_path: Path, cache_message: str = "") -> str:
    """Open a cached file given a file path"""
    print(cache_message)
    with file_path.open() as f:
        return f.read()


def create_caching_path(file_path: Path, cache_message: str = "") -> None:
    """Create the parent folder to save a cached file to"""
    print(cache_message)
    file_path.parent.mkdir(exist_ok=True, parents=True)


def cache_file(file_path: Path, file_contents: str, cache_message: str = "") -> None:
    """Creates a cache of a file"""
    print(cache_message)
    with file_path.open("w") as f:
        f.write(file_contents)
