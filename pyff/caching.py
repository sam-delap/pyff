"""Helper Functions related to handling file caching"""

from pathlib import Path
import requests
import time

CACHE_DIR = Path.home() / ".pyff"


def load_file_cache(file_path: Path, cache_message: str = "") -> str:
    """Open a cached file given a file path"""
    _print_cache_message(cache_message)
    with file_path.open() as f:
        return f.read()


def create_caching_path(file_path: Path, cache_message: str = "") -> None:
    """Create the parent folder to save a cached file to"""
    _print_cache_message(cache_message)
    file_path.parent.mkdir(exist_ok=True, parents=True)


def cache_file(file_path: Path, file_contents: str, cache_message: str = "") -> None:
    """Creates a cache of a file"""
    create_caching_path(file_path)
    _print_cache_message(cache_message)
    with file_path.open("w") as f:
        f.write(file_contents)


def _print_cache_message(cache_message):
    if cache_message != "":
        print(cache_message)


def handle_request(url: str, request_message: str = "") -> requests.Response:
    """Handle a request with baked-in error handling and sleep to comply with PFR rate-limits"""
    _print_cache_message(request_message)
    response = requests.get(url)
    time.sleep(6)
    if response.status_code != 200:
        raise requests.HTTPError(
            f"Request unsuccessful. Response code: {response.status_code}"
        )
    return response
