from .teams import Team
from .positions import QB, SkillPlayer

def main(filename: str, teams: list[str]=["all"]) -> None:
    if teams[0] == "all":
        teams = ["crd",
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

    for team_name in teams:
        team = Team(team_name)
        if input(f'Do you need to do projects for {team.team_name}?') == 'y': 
            team.project()
            team.save_projections(filename)
        project_teams_players(team, filename)
        fill_team_stats(team, filename)

def project_teams_players(team: Team, filename: str) -> None:
    qb_prompt_loop(team, filename)
    wr_prompt_loop(team, filename)
    rb_prompt_loop(team, filename)
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

def fill_team_stats(team: Team, filename: str):
    pass
