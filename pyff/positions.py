from datetime import date
from pathlib import Path
import requests
import time
from bs4 import BeautifulSoup, Comment, Tag
import pandas as pd
from .teams import Team

class QB:
    """Projection process for quarterbacks"""
    def __init__(self, team: Team):
        """Searches through QBs on a team's current roster until you want to project one, then collects historical data for the past 3 years about that player"""
        self.team = team
        self.current_year = date.today().year
        index = pd.Index(range(self.current_year - 3, self.current_year + 1))
        columns = ['pass_att',
                   'int %',
                   'pass td %',
                   'comp %',
                   'rush %',
                   'ypc',
                   'tds/rush_yard'
                   ]
        self.historical_data = pd.DataFrame(index=index, columns=columns)
        team_url = f'https://pro-football-reference.com/teams/{self.team.team_name}/{self.current_year}_roster.htm'
        response = requests.get(team_url)
        time.sleep(6)
        if response.status_code != 200:
            raise requests.HTTPError(f'Request unsuccessful. Response code: {response.status_code}')
        doc = BeautifulSoup(response.text, 'html.parser')
        
        player_div: Tag = doc.find('div', id='all_roster')
        
        for d in player_div.descendants:
            if isinstance(d, Comment):
                table_doc = BeautifulSoup(d.string, 'html.parser')

        table_rows = table_doc.find('tbody').find_all('tr')

        for row in table_rows:
            pos = row.find(attrs={'data-stat':'pos'}).get_text()
            if pos != 'QB':
                continue
            player_data = row.find(attrs={'data-stat':'player'})
            player_name = player_data.get_text()
            decision = input(f'Would you like to do projections for {player_name}? ').lower() == 'y'
            if decision:
                self.player_name = player_name
                player_url_suffix = player_data.find('a').get('href')
                player_url = f'https://pro-football-reference.com{player_url_suffix}'
                break

        if 'player_url' not in locals():
            raise NameError('No projections will be done for this team')
        if player_url is None:
            raise ValueError('Player URL undefined')

        response = requests.get(player_url)
        time.sleep(6)
        if response.status_code != 200:
            raise requests.HTTPError(f'Request unsuccessful. Response code: {response.status_code}')
        doc = BeautifulSoup(response.text, 'html.parser')
    
        for year in range(self.current_year - 3, self.current_year):
            passing_row = doc.find('table', id='passing').find('tbody').find('tr', id=f'passing.{year}')
            rushing_row = doc.find('table', id='rushing_and_receiving').find('tbody').find('tr', id=f'rushing_and_receiving.{year}')
            self.historical_data.loc[year, 'pass_att'] = float(passing_row.find(attrs={'data-stat':'pass_att'}).get_text())
            self.historical_data.loc[year, 'int %'] = float(passing_row.find(attrs={'data-stat':'pass_int_perc'}).get_text())
            self.historical_data.loc[year, 'pass td %'] = float(passing_row.find(attrs={'data-stat':'pass_td_perc'}).get_text())
            self.historical_data.loc[year, 'comp %'] = float(passing_row.find(attrs={'data-stat':'pass_cmp_perc'}).get_text())
            self.historical_data.loc[year, 'rush %'] = float(rushing_row.find(attrs={'data-stat':'rush_att'}).get_text()) / self.team.historical_data.loc[year, 'run_plays'] * 100
            self.historical_data.loc[year, 'ypc'] = float(rushing_row.find(attrs={'data-stat':'rush_yds_per_att'}).get_text())
            self.historical_data.loc[year, 'tds/rush_yard'] = int(rushing_row.find(attrs={'data-stat':'rush_td'}).get_text()) / float(rushing_row.find(attrs={'data-stat':'rush_yds'}).get_text())

        self.historical_data = self.historical_data.fillna(0).astype('float32')

    def project(self):
        """Prompts the user to enter projections for the current season"""
        print(self.historical_data)
        print('Average int %: ', self.historical_data['int %'].drop(self.current_year).mean())
        print('Average rush %: ', self.historical_data['rush %'].drop(self.current_year).mean())
        print('Average ypc: ', self.historical_data['ypc'].drop(self.current_year).mean())
        print('Average tds/rush_yard: ', self.historical_data['tds/rush_yard'].drop(self.current_year).mean())
        print()
        need_answer = True
        while need_answer:
            try:
                int_perc = input('Estimated int % for 2024: ')
                int_perc = float(int_perc)
                need_answer = False
            except ValueError:
                print('This is not a valid decimal!')
        need_answer = True
        while need_answer:
            try:
                rush_percent = input('Estimated rush % for 2024: ')
                rush_percent = float(rush_percent)
                need_answer = False
            except ValueError:
                print('This is not a valid decimal!')
        need_answer = True
        while need_answer:
            try:
                ypc = input('Estimated ypc for 2024: ')
                ypc = float(ypc)
                need_answer = False
            except ValueError:
                print('This is not a valid decimal!')
        need_answer = True
        while need_answer:
            try:
                td_yard_ratio = input('Estimated tds/rush_yard for 2024: ')
                td_yard_ratio = float(td_yard_ratio)
                need_answer = False
            except ValueError:
                print('This is not a valid decimal!')

        self.historical_data.loc[self.current_year, 'int %'] = int_perc
        self.historical_data.loc[self.current_year, 'rush_percent'] = rush_percent
        self.historical_data.loc[self.current_year, 'ypc'] = ypc
        self.historical_data.loc[self.current_year, 'tds/rush_yard'] = td_yard_ratio

    def save_projections(self, filename: str):
        """Saves your team-level projection to a sheet"""
        file_path = Path(filename)
        if not file_path.parent.exists: 
            file_path.parent.mkdir(parents=True)
            self.historical_data.loc[self.current_year, :].to_excel(filename, sheet_name=self.team.team_name.capitalize())
        else:
            existing_data = pd.read_excel(filename)
            df_combined = pd.concat([existing_data, self.historical_data.loc[self.current_year, :]])
            df_combined.to_excel(filename, sheet_name=self.team.team_name.capitalize())
