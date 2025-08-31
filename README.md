# pyff

Python-based fantasy football projection development tool

## Usage

### Full projections

If you're just looking to do projections for all 32 NFL teams and save them to Excel,
you can clone the code to your local machine and use the following command from the
root of the repo:

```bash
python3 -m pyff.cli <path/to/excel/file>
```

The script will walk you through prompts for team and player level statistics for
each team, calculate fantasy football projections for each player (based on the
scoring settings embedded in the environment variables), and create aggregated
rankings for each position (QB, WR, RB, TE).

### Re-calculating rankings

If you already have complete projections that you'd like to tune based on more
fundamental stats (work share, per-carry or per-catch metrics, etc.), tune those
in your Excel sheet, then run the following commands from the root of the repo

```bash
# Enter an interactive, terminal-based session of python (relies on the ipython package)
ipython
```

```python
from pyff.cli import fill_team_stats, create_fantasy_rankings

# Re-fill stats for a given team. Repeat for any teams you've adjusted
fill_team_stats('<team_str>', '<path/to/excel>')

# Run at the end once you're finished adjusting your stats
create_fantasy_rankings('<path/to/excel>')
```
