from bs4 import BeautifulSoup
import json
import os
import glob
import csv
import requests
import time

teams_data = []

def readKenPomHtml():
    # Read the HTML from the saved response file
    with open('/home/tmoran/personal/madness/src/model/response.txt', 'r') as f:
        html_content = f.read()

    soup = BeautifulSoup(html_content, 'html.parser')

    # Find the ratings table
    table = soup.find('table', {'id': 'ratings-table'})
    tbody = table.find('tbody')
    rows = tbody.find_all('tr')

    return rows

def parseFourFactors(year):
    rows = readKenPomHtml()
    for row in rows:
        cells = row.find_all('td')
        if(len(cells) < 23):
            continue  # Skip rows that don't have enough data
        
        # Extract team name
        team_name = cells[0].find('a').text.strip()
        
        # Extract conference
        conf = cells[1].find('a').text.strip()
        
        # Extract all the stats (values are in td-left class)
        adj_tempo = cells[2].text.strip()
        adj_oe = cells[4].text.strip()
        efg_pct_off = cells[6].text.strip()
        to_pct_off = cells[8].text.strip()
        or_pct_off = cells[10].text.strip()
        ft_rate_off = cells[12].text.strip()
        adj_de = cells[14].text.strip()
        efg_pct_def = cells[16].text.strip()
        to_pct_def = cells[18].text.strip()
        or_pct_def = cells[20].text.strip()
        ft_rate_def = cells[22].text.strip()
        
        team_dict = {
            "team": team_name,
            "conf": conf,
            "adjTempo": adj_tempo,
            "adjOE": adj_oe,
            "eFG_pct_off": efg_pct_off,
            "TO_pct_off": to_pct_off,
            "OR_pct_off": or_pct_off,
            "FTRate_off": ft_rate_off,
            "adjDE": adj_de,
            "eFG_pct_def": efg_pct_def,
            "TO_pct_def": to_pct_def,
            "OR_pct_def": or_pct_def,
            "FTRate_def": ft_rate_def
        }
        
        teams_data.append(team_dict)
        
    # Save to matchups folder
        ff_dir = '/home/tmoran/personal/madness/src/model/fourFactors/'
        
        output_file = os.path.join(ff_dir, f'{year}.json')
        with open(output_file, 'w') as f:
            json.dump(teams_data, f, indent=2)

def parseMiscStats(year):
    rows = readKenPomHtml()
    for row in rows:
        cells = row.find_all('td')
        if(len(cells) < 20):
            continue  # Skip rows that don't have enough data
        
        # Extract team name
        team_name = cells[0].find('a').text.strip()
        
        # Extract all the stats
        assist_index = 16
        three_pa_index = 18
        if year < 2022:
            assist_index = 14
            three_pa_index = 16
        
        three_p_pct = cells[2].text.strip()
        two_p_pct = cells[4].text.strip()
        ft_pct = cells[6].text.strip()
        blk_pct = cells[8].text.strip()
        stl_pct = cells[10].text.strip()
        a_pct = cells[assist_index].text.strip()
        three_pa_pct = cells[three_pa_index].text.strip()
        
        team_dict = {
            "team": team_name,
            "3P_pct": three_p_pct,
            "2P_pct": two_p_pct,
            "FT_pct": ft_pct,
            "Blk_pct": blk_pct,
            "Stl_pct": stl_pct,
            "A_pct": a_pct,
            "3PA_pct": three_pa_pct,
        }
        
        teams_data.append(team_dict)

    # Write teams_data to JSON file
    output_file = f"/home/tmoran/personal/madness/src/model/misc/{year}.json"
    with open(output_file, 'w') as f:
        json.dump(teams_data, f, indent=2)

    print(f"Successfully saved {len(teams_data)} teams to {output_file}")
    
def parseTeamNames():
    # Set to store unique team names
    team_names = set()
    
    # Path to the fourFactors folder
    four_factors_dir = '/home/tmoran/personal/madness/src/model/fourFactors/'
    
    # Get all JSON files in the fourFactors folder
    json_files = glob.glob(os.path.join(four_factors_dir, '*.json'))
    
    # Process each JSON file
    for json_file in json_files:
        with open(json_file, 'r') as f:
            data = json.load(f)
            
            # Extract team names from each file
            for team_entry in data:
                if 'team' in team_entry:
                    team_names.add(team_entry['team'])
    
    # Convert set to sorted list for better readability
    unique_teams = sorted(list(team_names))
    
    # Save to JSON file
    output_file = '/home/tmoran/personal/madness/src/model/teamNames.json'
    with open(output_file, 'w') as f:
        json.dump(unique_teams, f, indent=2)
    
    print(f"Successfully extracted {len(unique_teams)} unique teams to {output_file}")
    return unique_teams

def load_ratings(year):
    """Load team ratings for a given year."""
    ratings_file = f'/home/tmoran/personal/madness/src/model/ratings/{year}.json'
    if not os.path.exists(ratings_file):
        print(f"Warning: Ratings file not found for {year}")
        return {}
    
    with open(ratings_file, 'r') as f:
        ratings_data = json.load(f)
    
    # Create a dictionary mapping team name to {netRating, rank}
    ratings_dict = {}
    for entry in ratings_data:
        ratings_dict[entry['team']] = {
            'netRating': entry['netRating'],
            'rank': entry['rank']
        }
    
    return ratings_dict

def parseTournamentMatchups(yearsToAvoid=[], appendMode=False):
    # Load mismatched team names for validation
    mismatched_names = {}
    with open('/home/tmoran/personal/madness/src/model/util/mismatchedNames.json', 'r') as f:
        mismatched_names = json.load(f)
        
    team_ratings_by_year = {}

    # Read the CSV file
    csv_file = '/home/tmoran/personal/madness/src/model/util/TournamentMatchups.csv'
    all_rows = []
    
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            all_rows.append(row)
    
    # Process rows in pairs to create matchups
    matchups_by_year = {}
    
    i = 0
    while i < len(all_rows) - 1:
        row1 = all_rows[i]
        row2 = all_rows[i + 1]
        
        year = int(row1['YEAR'])
        
        # Skip 2025 since it doesn't have scores
        if year in yearsToAvoid:
            i += 2
            continue
        
        # Check if both rows are from the same year (sanity check)
        if int(row2['YEAR']) != year:
            i += 1
            continue
        
        if(year not in team_ratings_by_year):
            team_ratings_by_year[year] = load_ratings(year)
        
        # Extract team data
        team1_name = row1['TEAM']
        team2_name = row2['TEAM']
        seed1 = int(row1['SEED'])
        seed2 = int(row2['SEED'])
        score1 = int(row1['SCORE']) if row1['SCORE'] else None
        score2 = int(row2['SCORE']) if row2['SCORE'] else None
        rating1 = team_ratings_by_year[year].get(team1_name, {}).get('netRating', None)
        rank1 = team_ratings_by_year[year].get(team1_name, {}).get('rank', None)
        rating2 = team_ratings_by_year[year].get(team2_name, {}).get('netRating', None)
        rank2 = team_ratings_by_year[year].get(team2_name, {}).get('rank', None)
        
        # (outdated, first run code) check for mismatched team names
        '''
        if team1_name not in valid_team_names:
            mismatched_names.add(team1_name)
        if team2_name not in valid_team_names:
            mismatched_names.add(team2_name)
        '''
        if team1_name in mismatched_names:
            team1_name = mismatched_names[team1_name]
        if team2_name in mismatched_names:
            team2_name = mismatched_names[team2_name]
            
        # Determine higher/lower seeds (lower seed number = higher seed)
        if seed1 < seed2:
            higher_seed = seed1
            lower_seed = seed2
            higher_seed_team = team1_name
            lower_seed_team = team2_name
            higher_seed_score = score1
            lower_seed_score = score2
            higher_seed_rating = rating1
            lower_seed_rating = rating2
            higher_seed_rank = rank1
            lower_seed_rank = rank2
        else:
            higher_seed = seed2
            lower_seed = seed1
            higher_seed_team = team2_name
            lower_seed_team = team1_name
            higher_seed_score = score2
            lower_seed_score = score1
            higher_seed_rating = rating2
            lower_seed_rating = rating1
            higher_seed_rank = rank2
            lower_seed_rank = rank1
        
        # Determine winning team
        winning_team = None
        if score1 is not None and score2 is not None:
            if score1 > score2:
                winning_team = team1_name
            elif score2 > score1:
                winning_team = team2_name
        
        # Create matchup entry
        matchup_entry = {
            "year": year,
            "round": int(row1['CURRENT ROUND']),
            "higherSeed": higher_seed,
            "higherSeedTeam": higher_seed_team,
            "lowerSeed": lower_seed,
            "lowerSeedTeam": lower_seed_team,
            "higherSeedScore": higher_seed_score,
            "lowerSeedScore": lower_seed_score,
            "winningTeam": winning_team,
            "higherRating": higher_seed_rating,
            "lowerRating": lower_seed_rating,
            "higherRank": higher_seed_rank,
            "lowerRank": lower_seed_rank
        }
        
        # Initialize year list if not exists
        if year not in matchups_by_year:
            matchups_by_year[year] = []
        
        matchups_by_year[year].append(matchup_entry)
        
        i += 2  # Move to next pair
    
    # Create output directory if it doesn't exist
    matchups_dir = '/home/tmoran/personal/madness/src/model/matchups/'
    os.makedirs(matchups_dir, exist_ok=True)
    
    # Save each year's matchups to a separate JSON file
    for year, matchups in sorted(matchups_by_year.items()):
        output_file = os.path.join(matchups_dir, f'{year}.json')
        
        # If appendMode is True, load existing matchups and append new ones
        if appendMode and os.path.exists(output_file):
            with open(output_file, 'r') as f:
                existing_matchups = json.load(f)
            combined_matchups = existing_matchups + matchups
            with open(output_file, 'w') as f:
                json.dump(combined_matchups, f, indent=2)
            print(f"Appended {len(matchups)} matchups to existing {len(existing_matchups)} for {year} to {output_file}")
        else:
            with open(output_file, 'w') as f:
                json.dump(matchups, f, indent=2)
            print(f"Saved {len(matchups)} matchups for {year} to {output_file}")
    
    # (outdated, first run code) save mismatched names to a JSON file
    '''
    mismatched_output = '/home/tmoran/personal/madness/src/model/mismatchedNames.json'
    with open(mismatched_output, 'w') as f:
        json.dump(sorted(list(mismatched_names)), f, indent=2)
    
    print(f"\nFound {len(mismatched_names)} mismatched team names:")
    for name in sorted(mismatched_names):
        print(f"  - {name}")
    print(f"Saved to {mismatched_output}")
    '''

def extractUpsets():
    # Path to the matchups folder
    matchups_dir = '/home/tmoran/personal/madness/src/model/matchups/'
    
    # Get all JSON files in the matchups folder
    json_files = glob.glob(os.path.join(matchups_dir, '*.json'))
    
    # Process each JSON file
    for json_file in sorted(json_files):
        # Extract year from filename (e.g., matchups2024.json -> 2024)
        year = os.path.basename(json_file).replace('matchups', '').replace('.json', '')
        
        with open(json_file, 'r') as f:
            matchups = json.load(f)
        
        upsets = []
        
        for matchup in matchups:
            higher_seed = matchup['higherSeed']
            lower_seed = matchup['lowerSeed']
            higher_seed_team = matchup['higherSeedTeam']
            lower_seed_team = matchup['lowerSeedTeam']
            higher_seed_score = matchup['higherSeedScore']
            lower_seed_score = matchup['lowerSeedScore']
            winning_team = matchup['winningTeam']
            round_num = matchup['round']
            
            # Check if it's an upset (lower seed won and seed difference >= 5)
            if winning_team == lower_seed_team and (lower_seed - higher_seed) >= 5:
                upset_entry = {
                    "winningTeam": lower_seed_team,
                    "winningSeed": lower_seed,
                    "losingTeam": higher_seed_team,
                    "losingSeed": higher_seed,
                    "winningScore": lower_seed_score,
                    "losingScore": higher_seed_score,
                    "round": round_num
                }
                upsets.append(upset_entry)
        
        # Save upsets to JSON file if there are any
        if upsets:
            output_dir = '/home/tmoran/personal/madness/src/model/upsets/'
            os.makedirs(output_dir, exist_ok=True)
            output_file = os.path.join(output_dir, f'upsets{year}.json')
            with open(output_file, 'w') as f:
                json.dump(upsets, f, indent=2)
            print(f"Saved {len(upsets)} upsets for {year} to {output_file}")
        else:
            print(f"No upsets found for {year}")

def extractOlderMatchups():
    """
    Parse bracketData JSON files from 1997-2007 and convert them to matchups format
    """
    import glob
    import os
    import json
    
    # Path to bracketData folder
    bracket_data_dir = '/home/tmoran/personal/madness/src/model/bracketData/'
    
    # Years to process (1997-2007)
    years = range(1997, 2008)
    
    for year in years:
        bracket_file = os.path.join(bracket_data_dir, f'{year}.json')
        
        if not os.path.exists(bracket_file):
            print(f"Warning: {bracket_file} not found, skipping")
            continue
        
        with open(bracket_file, 'r') as f:
            bracket_data = json.load(f)
        
        matchups = []
        
        # Process regional rounds (4 regions)
        for region in bracket_data['regions']:
            # Each region has rounds: [round_of_64, round_of_32, round_of_16, round_of_8]
            for round_idx, round_data in enumerate(region):
                # Each round has matchups
                for matchup in round_data:
                    if len(matchup) == 2:  # Valid matchup pair
                        team1 = matchup[0]
                        team2 = matchup[1]
                        
                        # Determine higher/lower seed
                        seed1 = team1['seed']
                        seed2 = team2['seed']
                        
                        if seed1 < seed2:
                            higher_seed = seed1
                            lower_seed = seed2
                            higher_seed_team = team1['team']
                            lower_seed_team = team2['team']
                            higher_seed_score = team1['score']
                            lower_seed_score = team2['score']
                        else:
                            higher_seed = seed2
                            lower_seed = seed1
                            higher_seed_team = team2['team']
                            lower_seed_team = team1['team']
                            higher_seed_score = team2['score']
                            lower_seed_score = team1['score']
                        
                        # Determine winner
                        if team1['score'] > team2['score']:
                            winning_team = team1['team']
                        else:
                            winning_team = team2['team']
                        
                        matchup_entry = {
                            "year": year,
                            "round": team1['round_of'],
                            "higherSeed": higher_seed,
                            "higherSeedTeam": higher_seed_team,
                            "lowerSeed": lower_seed,
                            "lowerSeedTeam": lower_seed_team,
                            "higherSeedScore": higher_seed_score,
                            "lowerSeedScore": lower_seed_score,
                            "winningTeam": winning_team
                        }
                        
                        matchups.append(matchup_entry)
        
        # Skip final four rounds because we don't care about those upsets
        
        # Save to matchups folder
        matchups_dir = '/home/tmoran/personal/madness/src/model/matchups/'
        os.makedirs(matchups_dir, exist_ok=True)
        
        output_file = os.path.join(matchups_dir, f'{year}.json')
        with open(output_file, 'w') as f:
            json.dump(matchups, f, indent=2)
        
        print(f"Saved {len(matchups)} matchups for {year} to {output_file}")

def fetchTeamPage(team, cookie_value, year, cookie_name='PHPSESSID'):
    
    # Create cookie dictionary
    cookies = {cookie_name: cookie_value}
    
    # Make the GET request with the cookie
    url = f"https://kenpom.com/team.php?team={team}&y={year}"
    response = requests.get(url, verify=False, cookies=cookies)
    
    return response

def fetchTeamQuadPage(team, cookie_value):
    # Create headers with cookie string
    headers = {
        'Cookie': cookie_value
    }
    
    # Make the GET request with the cookie header
    url = f"https://bballnet.com/teams/{team}"
    response = requests.get(url, headers=headers, verify=False)
    
    return response

def fetchWabRankingsPage(year):
    """Fetch NCAA WAB rankings page HTML and save it to wabRankings{year}.txt."""
    url = "https://www.ncaa.com/rankings/basketball-men/d1/wab-ranking"
    response = requests.get(url, verify=False)
    response.raise_for_status()

    output_file = f"/home/tmoran/personal/madness/src/model/util/wabRankings{year}.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(response.text)

    print(f"Saved WAB rankings HTML to {output_file}")
    return response

namesToReplace = { 
    "SIUE": "southern-illinois-edwardsville",
    "VCU": "virginia-commonwealth",
    "McNeese": "mcneese-state",
    "BYU": "brigham-young",
    "UNC Wilmington": "north-carolina-wilmington",
    "Saint Francis": "saint-francis-pa",
    "Mount St. Mary's": "mount-st-marys",
    "Saint Mary's": "saint-marys-ca",
    "St. John's": "st-johns-ny",
    "UC San Diego": "california-san-diego",
    "NC State": "north-carolina-state",
    "SMU": "southern-methodist",
    "TCU": "texas-christian",
    "UCF": "central-florida",
    "USC": "southern-california",
    "LIU": "long-island-university",
    "Queens": "queens-nc",
}
def fetchTopTeams(given_top_teams, year, andRank=False, quads=False):
    """Fetch team pages for certain teams + year"""
    
    # Load ratings data
    ratings_file = f'/home/tmoran/personal/madness/src/model/ratings/{year}.json'
    with open(ratings_file, 'r') as f:
        ratings_data = json.load(f)
    
    # Filter teams with rank <= x
    if(andRank):
        top_teams = list(dict.fromkeys(given_top_teams + [team['team'] for team in ratings_data if team['rank'] <= 55]))
    else:
        top_teams = given_top_teams
    
    # Create output directory
    pageType = 'TeamQuads' if quads else 'TeamPhps'
    output_dir = f'/home/tmoran/personal/madness/src/model/util/temp{pageType}/{year}'
    os.makedirs(output_dir, exist_ok=True)
    
    # Cookie value (same as in the example)
    kp_cookie_value = "8c4ee60332aa59f9702ee907e4c13265; kenpomuser=timthemoran%40gmail.com; kenpomid=e737b70d840eb9550ec0af116336e51d; _ga_6DKK0E2CDM=GS2.1.s1771279291$o50$g1$t1771279291$j60$l0$h0; cf_clearance=779MHWii_xqDW8EmiH0_5zr5M.6Dl_YBlHecN.AwReU-1771279291-1.2.1.1-Et1_o4wjfV0Xp4aMSrqiC_PpZekkmrYLofp1cushTAMKmCMUA_Nlnb4hIaEsALg6d54XGAb26fqvH3rGel3rm2kRv4NbpcFhol4W4lLQq0xYhdhqPgMSoim8m8vqbLZJdmiFGMSN1AzK0DAGOAiFvAzkDDI0LvKE4EHSNbRjYkjvr_jIzzqLnM8HgIb5h5060nKtLYys20ayZyHELb2uJpkVC5DN_UJdNxp0fmXFKzc"
    cookie_value = "_ga=GA1.1.1416474417.1771279390; _ga_Y86RJEMBDJ=GS2.1.s1771282213$o2$g1$t1771282213$j60$l0$h0; FCCDCF=%5Bnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2C%5B%5B32%2C%22%5B%5C%22e0aa732c-d60b-4e82-a9a1-330abf1c839b%5C%22%2C%5B1771279391%2C201000000%5D%5D%22%5D%5D%5D; FCNEC=%5B%5B%22AKsRol85bHpwr-6Ifp9T2AaJuP7UKyaq5r2lm2j1T4rRrKAktSCzx5u2RRUwXB1_IRxyQ85eQeyhp25y3dqshVmqxFderK5FAA4Tqkd9HxSnSudv7eq6ZfBPzbGrXa89pgUZx-VVfVCqYTyvAcUwLtEdZhUnv5Mxzg%3D%3D%22%5D%5D; __gads=ID=3a4467c739d5d30f:T=1771279401:RT=1771282214:S=ALNI_MZ8xMLeS0OnZ1bKT7WfDVW5dBKWIw; __gpi=UID=000013392ee6b96b:T=1771279401:RT=1771282214:S=ALNI_MaF5mOiuoclzxWuaWFd0YnhNydRkw; __eoi=ID=2f7212625bab4b32:T=1771279401:RT=1771282214:S=AA-AfjY3LfwI27veAixkxlKTi7FJ"

    print(f"Fetching team pages for {len(top_teams)} teams...")
    
    # Fetch each team's page
    for name in top_teams:
        phpName = name.replace('&', '%26')
        if name in namesToReplace:
            quadName = namesToReplace[name]
        else:
            quadName = name.replace(' ', '-').replace('&', '').replace('.', '').replace("'", '').replace("St", "state") 
        
        try:
            safe_filename = name.replace(' ', '_').replace('.', '').replace("'", '')
            output_file = os.path.join(output_dir, f'{safe_filename}.txt')

            if os.path.exists(output_file):
                print(f"Skipping {name}; file already exists")
                continue
            
            response = fetchTeamQuadPage(quadName, cookie_value, year) if quads else fetchTeamPage(phpName, kp_cookie_value, year)
            # Save response to file
            # Replace spaces and special characters in filename
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(response.text)
            
            print(f"Saved to {output_file}")
            
        except Exception as e:
            print(f"Error fetching page for {name}: {e}")
        
        time.sleep(1) # avoid constant requests
    
    print(f"\nCompleted fetching {len(top_teams)} team pages")

teams_2025 = [
    "Wisconsin",
    "Utah St.",
    "Arkansas",
    "Texas",
    "Kansas",
    "High Point",
    "McNeese",
    "Texas A&M",
    "Purdue",
    "SIUE",
    "Nebraska Omaha",
    "Georgia",
    "UCLA",
    "Baylor",
    "New Mexico",
    "Michigan St.",
    "UNC Wilmington",
    "Oregon",
    "Kentucky",
    "Colorado St.",
    "Louisville",
    "Bryant",
    "Lipscomb",
    "Clemson",
    "Akron",
    "Oklahoma",
    "Auburn",
    "Florida",
    "Tennessee",
    "Montana",
    "Yale",
    "Xavier",
    "Marquette",
    "Norfolk St.",
    "Creighton",
    "Mississippi",
    "Maryland",
    "VCU",
    "Troy",
    "Arizona",
    "Illinois",
    "Liberty",
    "Houston",
    "BYU",
    "Saint Mary's",
    "Vanderbilt",
    "Memphis",
    "Robert Morris",
    "Alabama",
    "Missouri",
    "St. John's",
    "Texas Tech",
    "Mississippi St.",
    "Duke",
    "Michigan",
    "Connecticut",
    "Drake",
    "North Carolina",
    "Grand Canyon",
    "Saint Francis",
    "UC San Diego",
    "San Diego St.",
    "Iowa St.",
    "American",
    "Gonzaga",
    "Wofford",
    "Alabama St.",
    "Mount St. Mary's"
]
bids_2026 = ["North Dakota St.", "Tennessee St.", "LIU", "Northern Iowa", "Siena", "Wright St.", "Hofstra", "Queens"]
all_extras = teams_2025 + bids_2026
#fetchTopTeams(teams_2025, 2026, False, False)
fetchWabRankingsPage(2026)