from datetime import date
from pathlib import Path
import requests
import time
from bs4 import BeautifulSoup, Comment, NavigableString, Tag
import pandas as pd
from openpyxl import load_workbook
from .teams import Team, Position
from .caching import CACHE_DIR, load_file_cache, cache_file


class QB:
    """Projection process for quarterbacks"""

    # Position included to provide consistency across different implementations, not used for QB
    def __init__(
        self,
        team: Team,
        position: Position,
        use_cache: bool = True,
        save_results: bool = True,
    ):
        """Searches through QBs on a team's current roster until you want to project one, then collects historical data for the past 3 years about that player"""
        self.team = team
        self.current_year = date.today().year
        index = pd.Index(range(self.current_year - 3, self.current_year + 1))
        columns = [
            "team",
            "games played",
            "games started",
            "pass_att",
            "int %",
            "pass td %",
            "comp %",
            "rush %",
            "ypc",
            "tds/rush_yard",
        ]
        self.historical_data = pd.DataFrame(index=index, columns=columns)
        team_url = f"https://pro-football-reference.com/teams/{self.team.team_name}/{self.current_year}_roster.htm"

        # Check if team data already cached
        roster_path = (
            CACHE_DIR / self.team.team_name / f"roster_{self.current_year}.html"
        )
        # Pull from cache if using and cache hit
        if use_cache and roster_path.exists():
            roster_data = load_file_cache(
                roster_path,
                f"Using cache for {self.current_year} team roster for {self.team.team_name}...",
            )
            doc = BeautifulSoup(roster_data, "html.parser")
        else:
            # Fetch roster data from ProFootballReference if not cached
            print(
                f"Fetching {self.current_year} team roster for {self.team.team_name}..."
            )

            response = requests.get(team_url)
            time.sleep(6)
            if response.status_code != 200:
                raise requests.HTTPError(
                    f"Request unsuccessful. Response code: {response.status_code}"
                )

            if save_results:
                cache_file(
                    roster_path,
                    response.text,
                    f"Saving {self.current_year} team roster for {self.team.team_name}...",
                )

            doc = BeautifulSoup(response.text, "html.parser")

        player_div = doc.find("div", id="all_roster")
        if type(player_div) != Tag:
            raise TypeError("Player div not found. Look at HTML")

        # Find table of players
        table_doc = None
        for d in player_div.descendants:
            if isinstance(d, Comment):
                table_doc = BeautifulSoup(d.string, "html.parser")

        if table_doc is None:
            raise ValueError("Table not found")

        table_body = table_doc.find("tbody")
        if type(table_body) is not Tag:
            print(type(table_body))
            raise TypeError("Table body does not have expected type. Check HTML")

        table_rows = table_body.find_all("tr")
        if table_rows is None:
            print(table_body)
            raise ValueError("Table rows not found")

        print(f"Finding all QBs for {team.team_name}")
        player_name = None
        player_url = None
        qbs = []
        for row in table_rows:
            if type(row) is not Tag:
                print(type(row))
                raise TypeError("Table row does not have expected type. Check HTML")

            position_data = row.find(attrs={"data-stat": "pos"})
            if position_data is None:
                raise ValueError(
                    f"Couldn't find value for player position using data-stat pos"
                )

            position_value = position_data.get_text()
            if position_value not in Position:
                # Log that this position isn't supported
                continue

            position = Position(position_value)
            if position != Position.QB:
                continue

            player_data = row.find(attrs={"data-stat": "player"})
            if player_data is None:
                raise ValueError("Cant find data for player")
            player_name = player_data.get_text()
            print(player_name)
            qbs.append((player_name, player_data))

        for player_name, player_data in qbs:
            decision = (
                input(f"Would you like to do projections for {player_name}? ").lower()
                == "y"
            )
            if decision:
                self.player_name = player_name
                player_url_suffix = player_data.find("a").get("href")
                player_url = f"https://pro-football-reference.com{player_url_suffix}"
                break

        if player_url is None or player_name is None:
            print(f"No projections will be done for this instance of {position.value}")
            self.projections_exist = False
            return

        qb_path = CACHE_DIR / team.team_name / f"qb_{player_name.replace(' ', '')}.html"

        if use_cache and qb_path.exists():
            qb_data = load_file_cache(
                qb_path, f"Loading cached stats for QB {player_name}..."
            )
            doc = BeautifulSoup(qb_data, "html.parser")
        else:
            print(f"Fetching stats for QB {player_name}...")
            response = requests.get(player_url)
            time.sleep(6)
            if response.status_code != 200:
                raise requests.HTTPError(
                    f"Request unsuccessful. Response code: {response.status_code}"
                )

            if save_results:
                cache_file(
                    qb_path, response.text, f"Caching stats for QB {player_name}"
                )
            doc = BeautifulSoup(response.text, "html.parser")

        rushing_table = doc.find("table", id="rushing_and_receiving")
        if rushing_table is None:
            print("Rushing/receiving table does not exist... assuming player is rookie")
            self.projections_exist = True
            return
        assert type(rushing_table) == Tag

        for year in range(self.current_year - 3, self.current_year):
            passing_table = doc.find("table", id="passing")
            assert type(passing_table) == Tag

            passing_table_body = passing_table.find("tbody")
            assert type(passing_table_body) == Tag

            passing_row = passing_table_body.find("tr", id=f"passing.{year}")
            assert type(passing_row) == Tag

            rushing_row = rushing_table.find("tbody").find(
                "tr", id=f"rushing_and_receiving.{year}"
            )
            if rushing_row is None or passing_row is None:
                print(f"{self.player_name} does not have data for {year}")
                continue
            current_stat = rushing_row.find(
                attrs={"data-stat": "team_name_abbr"}
            ).get_text()
            if current_stat == "":
                self.historical_data.loc[year, "team"] = "NA"
            else:
                self.historical_data.loc[year, "team"] = current_stat

            current_stat = rushing_row.find(attrs={"data-stat": "games"}).get_text()
            if current_stat == "":
                self.historical_data.loc[year, "games played"] = "NA"
            else:
                self.historical_data.loc[year, "games played"] = int(current_stat)

            current_stat = rushing_row.find(
                attrs={"data-stat": "games_started"}
            ).get_text()
            if current_stat == "":
                self.historical_data.loc[year, "games started"] = "NA"
            else:
                self.historical_data.loc[year, "games started"] = int(current_stat)

            self.historical_data.loc[year, "pass_att"] = float(
                passing_row.find(attrs={"data-stat": "pass_att"}).get_text()
            )
            self.historical_data.loc[year, "int %"] = float(
                passing_row.find(attrs={"data-stat": "pass_int_pct"}).get_text()
            )
            self.historical_data.loc[year, "pass td %"] = float(
                passing_row.find(attrs={"data-stat": "pass_td_pct"}).get_text()
            )
            self.historical_data.loc[year, "comp %"] = float(
                passing_row.find(attrs={"data-stat": "pass_cmp_pct"}).get_text()
            )
            self.historical_data.loc[year, "rush %"] = (
                float(rushing_row.find(attrs={"data-stat": "rush_att"}).get_text())
                / self.team.historical_data.loc[year, "run_plays"]
                * 100
            )
            self.historical_data.loc[year, "ypc"] = float(
                rushing_row.find(attrs={"data-stat": "rush_yds_per_att"}).get_text()
            )
            self.historical_data.loc[year, "tds/rush_yard"] = int(
                rushing_row.find(attrs={"data-stat": "rush_td"}).get_text()
            ) / float(rushing_row.find(attrs={"data-stat": "rush_yds"}).get_text())

        self.projections_exist = True

    def project(self):
        """Prompts the user to enter projections for the current season"""
        print(self.historical_data)
        print(
            "Average games played: ",
            self.historical_data["games played"].dropna(how="all").mean(),
        )
        print(
            "Average int %: ",
            self.historical_data["int %"].drop(self.current_year).mean(),
        )
        print(
            "Average rush %: ",
            self.historical_data["rush %"].drop(self.current_year).mean(),
        )
        print(
            "Average ypc: ", self.historical_data["ypc"].drop(self.current_year).mean()
        )
        print(
            "Average tds/rush_yard: ",
            self.historical_data["tds/rush_yard"].drop(self.current_year).mean(),
        )
        print()
        need_answer = True
        while need_answer:
            try:
                games_started = input(
                    f"Estimated games played for {self.current_year}: "
                )
                games_started = int(games_started)
                need_answer = False
            except ValueError:
                print("This is not a valid integer!")
        need_answer = True
        while need_answer:
            try:
                int_percent = input(f"Estimated int % for {self.current_year}: ")
                int_percent = float(int_percent)
                need_answer = False
            except ValueError:
                print("This is not a valid decimal!")
        need_answer = True
        while need_answer:
            try:
                rush_percent = input(f"Estimated rush % for {self.current_year}: ")
                rush_percent = float(rush_percent)
                need_answer = False
            except ValueError:
                print("This is not a valid decimal!")
        need_answer = True
        while need_answer:
            try:
                ypc = input(f"Estimated ypc for {self.current_year}: ")
                ypc = float(ypc)
                need_answer = False
            except ValueError:
                print("This is not a valid decimal!")
        need_answer = True
        while need_answer:
            try:
                td_yard_ratio = input(
                    f"Estimated tds/rush_yard for {self.current_year}: "
                )
                td_yard_ratio = float(td_yard_ratio)
                need_answer = False
            except ValueError:
                print("This is not a valid decimal!")

        self.games_started = games_started
        self.int_percent = int_percent
        self.rush_percent = rush_percent
        self.ypc = ypc
        self.td_yard_ratio = td_yard_ratio

    def save_projections(self, filename: str):
        """Saves your team-level projection to a sheet"""
        file_path = Path(filename)
        if file_path.parent.exists:
            wb = load_workbook(filename)
            if self.team.team_name.capitalize() not in wb.sheetnames:
                wb.create_sheet(self.team.team_name.capitalize())
                wb.save(filename)
            existing_data = pd.read_excel(
                filename, sheet_name=self.team.team_name.capitalize()
            )
            print(existing_data)
            if "Player Name" in existing_data:
                current_index = existing_data["Player Name"].size + 1
            else:
                current_index = 2
        else:
            file_path.parent.mkdir(parents=True)
            current_index = 2

        formatted_data = pd.DataFrame()
        formatted_data.loc[current_index, "Pos"] = "QB"
        formatted_data.loc[current_index, "Player Name"] = self.player_name
        formatted_data.loc[current_index, "Games Started"] = self.games_started
        formatted_data.loc[current_index, "Interception %"] = self.int_percent
        formatted_data.loc[current_index, "Rush Share"] = self.rush_percent
        formatted_data.loc[current_index, "Yards/Carry"] = self.ypc
        formatted_data.loc[current_index, "TDs/Yard"] = self.td_yard_ratio
        print(formatted_data)
        if "existing_data" in locals():
            df_combined = pd.concat([existing_data, formatted_data])
            print(df_combined)
            with pd.ExcelWriter(
                filename, engine="openpyxl", mode="a", if_sheet_exists="replace"
            ) as writer:
                print("Merging data in excel...")
                df_combined.to_excel(
                    writer, sheet_name=self.team.team_name.capitalize(), index=False
                )
        else:
            with pd.ExcelWriter(
                filename, engine="openpyxl", mode="a", if_sheet_exists="replace"
            ) as writer:
                print("Saving new data in excel...")
                formatted_data.to_excel(
                    writer, sheet_name=self.team.team_name.capitalize(), index=False
                )
