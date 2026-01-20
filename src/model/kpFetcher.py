from bs4 import BeautifulSoup
import json
import os
import glob
import csv

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

def parseFourFactors():
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
    output_file = f"/home/tmoran/personal/madness/src/model/miscStats/misc{year}.json"
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

def parseTournamentMatchups():
    # Load team names for validation
    with open('/home/tmoran/personal/madness/src/model/teamNames.json', 'r') as f:
        valid_team_names = set(json.load(f))
    
    # Track mismatched names
    mismatched_names = set()
    
    # Read the CSV file
    csv_file = '/home/tmoran/personal/madness/src/model/TournamentMatchups.csv'
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
        if year == 2025:
            i += 2
            continue
        
        # Check if both rows are from the same year (sanity check)
        if int(row2['YEAR']) != year:
            i += 1
            continue
        
        # Extract team data
        team1_name = row1['TEAM']
        team2_name = row2['TEAM']
        seed1 = int(row1['SEED'])
        seed2 = int(row2['SEED'])
        score1 = int(row1['SCORE']) if row1['SCORE'] else None
        score2 = int(row2['SCORE']) if row2['SCORE'] else None
        
        # Check for mismatched team names
        if team1_name not in valid_team_names:
            mismatched_names.add(team1_name)
        if team2_name not in valid_team_names:
            mismatched_names.add(team2_name)
        
        # Determine higher/lower seeds (lower seed number = higher seed)
        if seed1 < seed2:
            higher_seed = seed1
            lower_seed = seed2
            higher_seed_team = team1_name
            lower_seed_team = team2_name
            higher_seed_score = score1
            lower_seed_score = score2
        else:
            higher_seed = seed2
            lower_seed = seed1
            higher_seed_team = team2_name
            lower_seed_team = team1_name
            higher_seed_score = score2
            lower_seed_score = score1
        
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
            "winningTeam": winning_team
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
        output_file = os.path.join(matchups_dir, f'matchups{year}.json')
        with open(output_file, 'w') as f:
            json.dump(matchups, f, indent=2)
        print(f"Saved {len(matchups)} matchups for {year} to {output_file}")
    
    # Save mismatched names to a JSON file
    mismatched_output = '/home/tmoran/personal/madness/src/model/mismatchedNames.json'
    with open(mismatched_output, 'w') as f:
        json.dump(sorted(list(mismatched_names)), f, indent=2)
    
    print(f"\nFound {len(mismatched_names)} mismatched team names:")
    for name in sorted(mismatched_names):
        print(f"  - {name}")
    print(f"Saved to {mismatched_output}")

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

extractOlderMatchups()