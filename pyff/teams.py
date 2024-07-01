from datetime import date
from pathlib import Path
import requests
from bs4 import BeautifulSoup
import pandas as pd

pd.set_option('future.no_silent_downcasting', True)

class Team:
    """Fetches information about play percentage and rate-of-play over the last 3 years for a given team"""
    def __init__(self, team_name: str):
        self.team_name = team_name
        self.current_year = date.today().year
        index = pd.Index(range(self.current_year - 3, self.current_year + 1))
        columns = ['head_coach',
                   'offensive_coordinator',
                   'total_plays',
                   'run_percent',
                   'pass_percent']
        dtypes = {
                'head_coach': 'string',
                'offensive_coordinator': 'string',
                'total_plays': 'int32',
                'run_percent': 'float32',
                'pass_percent': 'float32'
        }
        self.historical_data = pd.DataFrame(index=index, columns=columns) 
        for year in self.historical_data.index:
            team_url = f'https://pro-football-reference.com/teams/{team_name}/{year}.htm'
            response = requests.get(team_url)
            if response.status_code != 200:
                raise HTTPError('Request unsuccessful')
            doc = BeautifulSoup(response.text, 'html.parser')
            if year != self.current_year:
                run_plays = int(doc.find('tbody').find('tr').find(attrs = {'data-stat': 'rush_att'}).text)
                pass_plays = int(doc.find('tbody').find('tr').find(attrs = {'data-stat': 'pass_att'}).text)
                total_plays: int = run_plays + pass_plays
                self.historical_data.loc[year, 'total_plays'] = total_plays
                self.historical_data.loc[year, 'run_percent'] = round(run_plays / total_plays * 100, 2)
                self.historical_data.loc[year, 'pass_percent'] = round(pass_plays / total_plays * 100, 2)
            for p in doc.find_all('p'):
                if "Coach:" in p.get_text():
                    self.historical_data.loc[year, 'head_coach'] = p.find('a').get_text()
                elif "Offensive Coordinator:" in p.get_text():
                    self.historical_data.loc[year, 'offensive_coordinator'] = p.find('a').get_text()

        self.historical_data = self.historical_data.fillna(0).astype(dtypes)

    def project(self):
        """Prompts the user to enter projections for the current season"""
        print(self.historical_data)
        print('Average plays: ', self.historical_data['total_plays'].drop(self.current_year).mean())
        print('Average run %: ', self.historical_data['run_percent'].drop(self.current_year).mean())
        print('Average pass %: ', self.historical_data['pass_percent'].drop(self.current_year).mean())
        print()
        need_answer = True
        while need_answer:
            try:
                plays = input('Estimated plays for 2024: ')
                plays = int(plays)
                need_answer = False
            except ValueError:
                print('This is not a valid integer!')
        need_answer = True
        while need_answer:
            try:
                run_percent = input('Estimated run % for 2024: ')
                run_percent = float(run_percent)
                need_answer = False
            except ValueError:
                print('This is not a valid decimal!')
        need_answer = True
        while need_answer:
            try:
                pass_percent = input('Estimated pass % for 2024: ')
                pass_percent = float(pass_percent)
                need_answer = False
            except ValueError:
                print('This is not a valid decimal!')

        self.historical_data.loc[self.current_year, 'total_plays'] = plays
        self.historical_data.loc[self.current_year, 'run_percent'] = run_percent
        self.historical_data.loc[self.current_year, 'pass_percent'] = pass_percent

    def save_projections(self, filename: str):
        """Saves your team-level projection to a sheet"""
        file_path = Path(filename)
        file_path.parent.mkdir(parents=True)
        self.historical_data.loc[self.current_year, :].to_excel(filename, sheet_name=self.team_name.capitalize())
