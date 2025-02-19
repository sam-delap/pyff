import pandas as pd

from .teams import Team
from .positions import QB, SkillPlayer

ALL_TEAMS = ["crd",
            "atl",
            "rav",
            "buf",
            "car",
            "chi",
            "cin",
            "cle",
            "dal",
            "den",
            "det",
            "gnb",
            "htx",
            "clt",
            "jax",
            "kan",
            "rai",
            "sdg",
            "ram",
            "mia",
            "min",
            "nwe",
            "nor",
            "nyg",
            "nyj",
            "phi",
            "pit",
            "sfo",
            "sea",
            "tam",
            "oti",
            "was"]

# League-wide scoring settings
PASS_TD = 6
PASS_YD = 0.04
RUSH_REC_TD = 6
RUSH_REC_YD =  0.1
INTERCEPTION = -2
REC = 1

def main(filename: str, teams: list[str]=["all"]) -> None:
    if teams[0] == "all":
        teams = ALL_TEAMS
    for team_name in teams:
        if not input(f'Would you like to project team {team_name}? ') == 'y':
            continue
        team = Team(team_name)
        if input(f'Do you need to do team-level projections for {team.team_name}? ') == 'y': 
            team.project()
            team.save_projections(filename)
        project_teams_players(team, filename)
        fill_team_stats(team_name, filename)

    create_fantasy_rankings(filename, teams)

def project_teams_players(team: Team, filename: str) -> None:
    if input(f'Do you need to do QB projections for {team.team_name}? ') == 'y':
        qb_prompt_loop(team, filename)
    if input(f'Do you need to do WR projections for {team.team_name}? ') == 'y':
        wr_prompt_loop(team, filename)
    if input(f'Do you need to do RB projections for {team.team_name}? ') == 'y':
        rb_prompt_loop(team, filename)
    if input(f'Do you need to do TE projections for {team.team_name}? ') == 'y':
        te_prompt_loop(team, filename)

def qb_prompt_loop(team: Team, filename: str) -> None:
    should_continue = True
    while should_continue:
        qb = QB(team)
        if qb.projections_exist:
            qb.project()
            qb.save_projections(filename)
        should_continue = input(f'Would you like to project another QB for {team.team_name}? ') == 'y'
    
def wr_prompt_loop(team: Team, filename: str):
    should_continue = True
    while should_continue:
        wr = SkillPlayer(team, 'WR')
        if wr.projections_exist:
            wr.project()
            wr.save_projections(filename)
        should_continue = input(f'Would you like to project another WR for {team.team_name}? ') == 'y'

def rb_prompt_loop(team: Team, filename: str):
    should_continue = True
    while should_continue:
        rb = SkillPlayer(team, 'RB')
        if rb.projections_exist:
            rb.project()
            rb.save_projections(filename)
        should_continue = input(f'Would you like to project another RB for {team.team_name}? ') == 'y'

def te_prompt_loop(team: Team, filename: str):
    should_continue = True
    while should_continue:
        te = SkillPlayer(team, 'TE')
        if te.projections_exist:
            te.project()
            te.save_projections(filename)
        should_continue = input(f'Would you like to project another TE for {team.team_name}? ') == 'y'

def fill_team_stats(team_name: str, filename: str):
    team_df = pd.read_excel(filename, sheet_name=team_name.capitalize())

    run_plays = team_df['Run Plays'][0]
    pass_plays = team_df['Pass Plays'][0]

    # Remainder calculation
    other_players_index = team_df['Player Name'].size + 2
    team_df.loc[other_players_index, 'Pos'] = 'WR/RB/TE'
    team_df.loc[other_players_index, 'Player Name'] = 'Other Players'
    team_df.loc[other_players_index, 'Games Started'] = 17
    team_df.loc[other_players_index, 'Rush Share'] = 100 - team_df['Rush Share'].sum()
    if team_df.loc[other_players_index, 'Rush Share'] < 0:
        print(f'Too many carries allocated for team {team_name}.')
    team_df.loc[other_players_index, 'Yards/Carry'] = 4.2
    team_df.loc[other_players_index, 'TDs/Yard'] = 0.006
    team_df.loc[other_players_index, 'Target Share'] = 100 - team_df['Target Share'].sum()
    if team_df.loc[other_players_index, 'Target Share'] < 0:
        print(f'Too many targets allocated for team {team_name}.')
    team_df.loc[other_players_index, 'Catch Percentage'] = 62
    team_df.loc[other_players_index, 'Yards/Catch'] = 11
    team_df.loc[other_players_index, 'TDs/receiving yard'] = 0.006

    # Rushing stats
    team_df['Carries'] = team_df['Rush Share'] / 100 * run_plays
    team_df['Rushing Yards'] = team_df['Yards/Carry'] * team_df['Carries']
    team_df['Rushing TDs'] = team_df['Rushing Yards'] * team_df['TDs/Yard']

    # Receiving stats
    team_df['Targets'] = team_df['Target Share'] / 100 * pass_plays
    team_df['Receptions'] = team_df['Targets'] * team_df['Catch Percentage'] / 100
    team_df['Receiving Yards'] = team_df['Receptions'] * team_df['Yards/Catch']
    team_df['Receiving TDs'] = team_df['Receiving Yards'] * team_df['TDs/receiving yard']

    # Passing stats (QB-dependent)
    is_qb = team_df['Pos'] == 'QB'
    team_df.loc[is_qb, 'Passing Attempts'] = team_df.loc[is_qb, 'Games Started'] / 17 * pass_plays
    team_df.loc[is_qb, 'Interceptions'] = team_df['Passing Attempts'] * team_df['Interception %'] / 100

    # Passing stats (skill player-dependent)
    team_df.loc[is_qb, 'Completions'] = team_df['Receptions'].sum() * team_df.loc[is_qb, 'Games Started'] / 17
    team_df.loc[is_qb, 'Completion %'] = team_df['Completions'] / team_df['Passing Attempts'] * 100
    if (team_df['Completion %'] > 70).any():
        print(f'Completion percentage too high for team {team_name}')
    team_df.loc[is_qb, 'Passing Yards'] = team_df['Receiving Yards'].sum() * team_df.loc[is_qb, 'Games Started'] / 17
    team_df.loc[is_qb, 'Passing TDs'] = team_df['Receiving TDs'].sum() * team_df.loc[is_qb, 'Games Started'] / 17
    team_df.loc[is_qb, 'Passing TD %'] = team_df['Passing TDs'] / team_df['Passing Attempts'] * 100
    if (team_df['Passing TD %'] > 8).any():
        print(f'Passing TD percentage too high for team {team_name}')

    # Fantasy points
    team_df['Fantasy Points'] = (
            team_df['Rushing Yards'].fillna(0) * RUSH_REC_YD
            + team_df['Rushing TDs'].fillna(0) * RUSH_REC_TD
            + team_df['Receptions'].fillna(0) * REC
            + team_df['Receiving Yards'].fillna(0) * RUSH_REC_YD
            + team_df['Receiving TDs'].fillna(0) * RUSH_REC_TD
            + team_df['Interceptions'].fillna(0) * INTERCEPTION
            + team_df['Passing Yards'].fillna(0) * PASS_YD
            + team_df['Passing TDs'].fillna(0) * PASS_TD
            )

    with pd.ExcelWriter(filename, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
        print('Saving projections in excel...')
        team_df.to_excel(writer, sheet_name=team_name.capitalize(), index=False)

def create_fantasy_rankings(filename: str, teams: list[str]=["all"]):
    if teams[0] == "all":
        teams = ALL_TEAMS
    for pos in ['QB', 'WR', 'RB', 'TE']:
        rankings_df = pd.DataFrame()
        for team_name in teams:
            current_team = pd.read_excel(filename, sheet_name=team_name.capitalize())
            is_pos = current_team['Pos'] == pos
            rankings_df = pd.concat([rankings_df, current_team.loc[is_pos, ['Player Name', 'Fantasy Points']]])

        rankings_df.sort_values('Fantasy Points', ascending=False, inplace=True)

        with pd.ExcelWriter(filename, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
            print(f'Saving {pos} rankings in excel...')
            rankings_df.to_excel(writer, sheet_name=pos, index=False)
