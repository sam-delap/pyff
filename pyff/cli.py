import pandas as pd
import argparse

from .teams import Team, Positions
from .quarterback import QB
from .skill_player import SkillPlayer

ALL_TEAMS = [
    "crd",
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
    "was",
]

# League-wide scoring settings
PASS_TD = 6
PASS_YD = 0.04
RUSH_REC_TD = 6
RUSH_REC_YD = 0.1
INTERCEPTION = -2
REC = 1


def main(filename: str, teams: list[str] = ["all"]) -> None:
    """Driver function"""
    if teams[0] == "all":
        teams = ALL_TEAMS
    for team_name in teams:
        if not input(f"Would you like to project team {team_name}? ") == "y":
            continue
        team = Team(team_name)
        if (
            input(f"Do you need to do team-level projections for {team.team_name}? ")
            == "y"
        ):
            team.project()
            team.save_projections(filename)
        for position in Positions:
            project_position(team, filename, position)
        fill_team_stats(team_name, filename)

    create_fantasy_rankings(filename, teams)


def project_position(team: Team, filename: str, position: Positions) -> None:
    """Project a given position"""
    if position == Positions.QB:
        player_class_to_create = QB
    else:
        player_class_to_create = SkillPlayer
    if (
        input(f"Do you need to do {position.value} projections for {team.team_name}? ")
        == "y"
    ):
        should_continue = True
        while should_continue:
            project_player(player_class_to_create, team, position, filename)
            should_continue = (
                input(
                    f"Would you like to project another {position.value} for {team.team_name}? "
                )
                == "y"
            )


def project_player(
    player_class: type, team: Team, position: Positions, filename: str
) -> None:
    player = player_class(team, position)
    if player.projections_exist:
        player.project()
        player.save_projections(filename)


def fill_team_stats(team_name: str, filename: str):
    team_df = pd.read_excel(filename, sheet_name=team_name.capitalize())

    run_plays = team_df["Run Plays"][0]
    pass_plays = team_df["Pass Plays"][0]

    # Remainder calculation
    other_players_index = team_df["Player Name"].size + 2
    team_df.loc[other_players_index, "Pos"] = "WR/RB/TE"
    team_df.loc[other_players_index, "Player Name"] = "Other Players"
    team_df.loc[other_players_index, "Games Started"] = 17
    team_df.loc[other_players_index, "Rush Share"] = 100 - team_df["Rush Share"].sum()
    if team_df.loc[other_players_index, "Rush Share"] < 0:
        print(f"Too many carries allocated for team {team_name}.")
    team_df.loc[other_players_index, "Yards/Carry"] = 4.2
    team_df.loc[other_players_index, "TDs/Rush Yard"] = 0.006
    team_df.loc[other_players_index, "Target Share"] = (
        100 - team_df["Target Share"].sum()
    )
    if team_df.loc[other_players_index, "Target Share"] < 0:
        print(f"Too many targets allocated for team {team_name}.")
    team_df.loc[other_players_index, "Catch Percentage"] = 62
    team_df.loc[other_players_index, "Yards/Catch"] = 11
    team_df.loc[other_players_index, "TDs/Receiving Yard"] = 0.006

    # Rushing stats
    team_df["Carries"] = team_df["Rush Share"] / 100 * run_plays
    team_df["Rushing Yards"] = team_df["Yards/Carry"] * team_df["Carries"]
    team_df["Rushing TDs"] = team_df["Rushing Yards"] * team_df["TDs/Rush Yard"]

    # Receiving stats
    team_df["Targets"] = team_df["Target Share"] / 100 * pass_plays
    team_df["Receptions"] = team_df["Targets"] * team_df["Catch Percentage"] / 100
    team_df["Receiving Yards"] = team_df["Receptions"] * team_df["Yards/Catch"]
    team_df["Receiving TDs"] = (
        team_df["Receiving Yards"] * team_df["TDs/Receiving Yard"]
    )

    # Passing stats (QB-dependent)
    is_qb = team_df["Pos"] == "QB"
    team_df.loc[is_qb, "Passing Attempts"] = (
        team_df.loc[is_qb, "Games Started"] / 17 * pass_plays
    )
    team_df.loc[is_qb, "Interceptions"] = (
        team_df["Passing Attempts"] * team_df["Interception %"] / 100
    )

    # Passing stats (skill player-dependent)
    team_df.loc[is_qb, "Completions"] = (
        team_df["Receptions"].sum() * team_df.loc[is_qb, "Games Started"] / 17
    )
    team_df.loc[is_qb, "Completion %"] = (
        team_df["Completions"] / team_df["Passing Attempts"] * 100
    )
    if (team_df["Completion %"] > 70).any():
        print(f"Completion percentage too high for team {team_name}")
    team_df.loc[is_qb, "Passing Yards"] = (
        team_df["Receiving Yards"].sum() * team_df.loc[is_qb, "Games Started"] / 17
    )
    team_df.loc[is_qb, "Passing TDs"] = (
        team_df["Receiving TDs"].sum() * team_df.loc[is_qb, "Games Started"] / 17
    )
    team_df.loc[is_qb, "Passing TD %"] = (
        team_df["Passing TDs"] / team_df["Passing Attempts"] * 100
    )
    if (team_df["Passing TD %"] > 8).any():
        print(f"Passing TD percentage too high for team {team_name}")

    # Fantasy points
    team_df["Fantasy Points"] = (
        team_df["Rushing Yards"].fillna(0) * RUSH_REC_YD
        + team_df["Rushing TDs"].fillna(0) * RUSH_REC_TD
        + team_df["Receptions"].fillna(0) * REC
        + team_df["Receiving Yards"].fillna(0) * RUSH_REC_YD
        + team_df["Receiving TDs"].fillna(0) * RUSH_REC_TD
        + team_df["Interceptions"].fillna(0) * INTERCEPTION
        + team_df["Passing Yards"].fillna(0) * PASS_YD
        + team_df["Passing TDs"].fillna(0) * PASS_TD
    )

    with pd.ExcelWriter(
        filename, engine="openpyxl", mode="a", if_sheet_exists="replace"
    ) as writer:
        print("Saving projections in excel...")
        team_df.to_excel(writer, sheet_name=team_name.capitalize(), index=False)


def create_fantasy_rankings(filename: str, teams: list[str] = ["all"]):
    if teams[0] == "all":
        teams = ALL_TEAMS
    for pos in ["QB", "WR", "RB", "TE"]:
        rankings_df = pd.DataFrame()
        for team_name in teams:
            current_team = pd.read_excel(filename, sheet_name=team_name.capitalize())
            is_pos = current_team["Pos"] == pos
            rankings_df = pd.concat(
                [
                    rankings_df,
                    current_team.loc[is_pos, ["Player Name", "Fantasy Points"]],
                ]
            )

        rankings_df.sort_values("Fantasy Points", ascending=False, inplace=True)

        with pd.ExcelWriter(
            filename, engine="openpyxl", mode="a", if_sheet_exists="replace"
        ) as writer:
            print(f"Saving {pos} rankings in excel...")
            rankings_df.to_excel(writer, sheet_name=pos, index=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Module entrypoint to do CLI-based fantasy football projections via pyff"
    )
    parser.add_argument(
        "filepath",
        help="Path to the Excel file where you want to store your final projections",
    )
    args = parser.parse_args()

    main(args.filepath)
