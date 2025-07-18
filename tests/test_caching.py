"""Test caching-related behaviors"""

from datetime import date
import shutil
from pyff.teams import Team
from pyff.caching import CACHE_DIR


def test_team_caching():
    Team("crd")
    current_year = date.today().year
    assert (CACHE_DIR / "crd" / f"team_{current_year}.html").exists()
    shutil.rmtree(CACHE_DIR / "crd")
