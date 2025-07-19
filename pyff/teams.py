from datetime import date
from enum import Enum
from pathlib import Path
import requests
import time

from bs4 import BeautifulSoup
import pandas as pd
from openpyxl import load_workbook, Workbook

from .caching import CACHE_DIR, load_file_cache, create_caching_path, cache_file

pd.set_option("future.no_silent_downcasting", True)


class Position(Enum):
    """Position enum for more self-documenting and type-safe position refs"""

    QB = "QB"
    WR = "WR"
    RB = "RB"
    TE = "TE"


class Team:
    """Fetches information about play percentage and rate-of-play over the last 3 years for a given team"""

    def __init__(
        self, team_name: str, use_cache: bool = True, save_results: bool = True
    ):
        self.team_name = team_name
        self.current_year = date.today().year
        index = pd.Index(range(self.current_year - 3, self.current_year + 1))
        columns = [
            "head_coach",
            "offensive_coordinator",
            "total_plays",
            "run_percent",
            "run_plays",
            "pass_percent",
            "pass_plays",
        ]
        dtypes = {
            "head_coach": "string",
            "offensive_coordinator": "string",
            "total_plays": "int32",
            "run_percent": "float32",
            "run_plays": "int32",
            "pass_percent": "float32",
            "pass_plays": "int32",
        }
        self.historical_data = pd.DataFrame(index=index, columns=columns)
        for year in self.historical_data.index:
            team_path = CACHE_DIR / self.team_name / f"team_{year}.html"
            if use_cache and team_path.exists():
                team_data = load_file_cache(
                    team_path, f"Using cache for {team_name} stats for {year}..."
                )
                doc = BeautifulSoup(team_data, "html.parser")
            else:
                team_url = (
                    f"https://pro-football-reference.com/teams/{team_name}/{year}.htm"
                )
                print(f"Looking up {team_name} stats for {year}...")
                response = requests.get(team_url)
                time.sleep(6)
                if response.status_code != 200:
                    raise requests.HTTPError(
                        f"Request unsuccessful. Response code: {response.status_code}"
                    )

                if save_results:
                    cache_file(
                        team_path,
                        response.text,
                        f"Saving {team_name} stats for {year}...",
                    )
                doc = BeautifulSoup(response.text, "html.parser")
            if year != self.current_year:
                run_plays = int(
                    doc.find("tbody")
                    .find("tr")
                    .find(attrs={"data-stat": "rush_att"})
                    .text
                )
                pass_plays = int(
                    doc.find("tbody")
                    .find("tr")
                    .find(attrs={"data-stat": "pass_att"})
                    .text
                )
                total_plays: int = run_plays + pass_plays
                self.historical_data.loc[year, "total_plays"] = total_plays
                self.historical_data.loc[year, "run_percent"] = round(
                    run_plays / total_plays * 100, 2
                )
                self.historical_data.loc[year, "pass_percent"] = round(
                    pass_plays / total_plays * 100, 2
                )
                self.historical_data.loc[year, "run_plays"] = run_plays
                self.historical_data.loc[year, "pass_plays"] = pass_plays
            for p in doc.find_all("p"):
                if "Coach:" in p.get_text():
                    self.historical_data.loc[year, "head_coach"] = p.find(
                        "a"
                    ).get_text()
                elif "Offensive Coordinator:" in p.get_text():
                    self.historical_data.loc[year, "offensive_coordinator"] = p.find(
                        "a"
                    ).get_text()

        self.historical_data = self.historical_data.fillna(0).astype(dtypes)

    def project(self):
        """Prompts the user to enter projections for the current season"""
        print(self.historical_data)
        print(
            "Average plays: ",
            self.historical_data["total_plays"].drop(self.current_year).mean(),
        )
        print(
            "Average run %: ",
            self.historical_data["run_percent"].drop(self.current_year).mean(),
        )
        print(
            "Average pass %: ",
            self.historical_data["pass_percent"].drop(self.current_year).mean(),
        )
        print()
        need_answer = True
        while need_answer:
            try:
                plays = input("Estimated plays for 2024: ")
                plays = int(plays)
                need_answer = False
            except ValueError:
                print("This is not a valid integer!")
        need_answer = True
        while need_answer:
            try:
                run_percent = input("Estimated run % for 2024: ")
                run_percent = float(run_percent)
                need_answer = False
            except ValueError:
                print("This is not a valid decimal!")
        need_answer = True
        while need_answer:
            try:
                pass_percent = input("Estimated pass % for 2024: ")
                pass_percent = float(pass_percent)
                need_answer = False
            except ValueError:
                print("This is not a valid decimal!")

        self.total_plays = plays
        self.run_percent = run_percent
        self.pass_percent = pass_percent

    def save_projections(self, filename: str):
        """Saves your team-level projection to a sheet"""
        file_path = Path(filename)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        if not file_path.exists():
            workbook = Workbook()
            workbook.create_sheet(self.team_name.capitalize())
            workbook.save(file_path)
            current_index = 1
        else:
            wb = load_workbook(filename)
            if self.team_name.capitalize() not in wb.sheetnames:
                wb.create_sheet(self.team_name.capitalize())
                wb.save(filename)
            existing_data = pd.read_excel(
                filename, sheet_name=self.team_name.capitalize()
            )
            current_index = existing_data.shape[0] + 1
        formatted_data = pd.DataFrame()
        formatted_data.loc[current_index, "Total Plays"] = self.total_plays
        formatted_data.loc[current_index, "Run Plays"] = round(
            self.total_plays * self.run_percent / 100, 2
        )
        formatted_data.loc[current_index, "Pass Plays"] = round(
            self.total_plays * self.pass_percent / 100, 2
        )
        if current_index > 1:
            print(existing_data)
            df_combined = pd.concat([existing_data, formatted_data])
            print(df_combined)
            with pd.ExcelWriter(
                filename, engine="openpyxl", mode="a", if_sheet_exists="replace"
            ) as writer:
                print("Merging data in excel...")
                df_combined.to_excel(
                    writer, sheet_name=self.team_name.capitalize(), index=False
                )
        else:
            with pd.ExcelWriter(
                filename, engine="openpyxl", mode="a", if_sheet_exists="replace"
            ) as writer:
                print("Saving new data to excel...")
                formatted_data.to_excel(
                    writer, sheet_name=self.team_name.capitalize(), index=False
                )
