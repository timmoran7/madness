import json
import os
from datetime import datetime

def load_mismatched_names():
    """Load the mismatched names mapping."""
    with open('/home/tmoran/personal/madness/src/model/util/mismatchedNames.json', 'r') as f:
        return json.load(f)

def normalize_team_name(team_name, mismatched_names):
    """Convert team name using mismatched names mapping if needed."""
    return mismatched_names.get(team_name, team_name)

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

def parse_game_line(line, year, ratings_dict, mismatched_names, gameCtr):
    """Parse a single game line from the txt file."""
    parts = line.split()
    
    # Parse date (MM/DD/YYYY format)
    date_str = parts[0]
    try:
        game_date = datetime.strptime(date_str, '%m/%d/%Y')
        
        # Ignore games between 3/14 and 5/1
        month = game_date.month
        day = game_date.day
        
        # After March 14 and before May 1
        if (month == 3 and day > 14) or month == 4:
            return None
            
    except ValueError:
        print('value error')
        return None
    
    # Find the scores (they are integers)
    score_indices = []
    for i, part in enumerate(parts):
        if part.isdigit() or (part.startswith('-') and part[1:].isdigit()):
            score_indices.append(i)
    
    if len(score_indices) < 2:
        return None
    
    if(len(score_indices) > 2):
        parts.pop(score_indices[2])
        
    if(len(score_indices) > 3):
        print('im curious', parts)
        parts.pop(score_indices[3])
    
    # The two scores should be near the end
    # Typically format is: Date Team1Name Score1 Team2Name Score2 [Location]
    score1_idx = score_indices[0]
    score2_idx = score_indices[1]
    
    isNeutral = False
    if len(parts[score2_idx:]) > 1:
        isNeutral = True
        location = ' '.join(parts[score2_idx + 2:])
    
    # Extract team names
    team1_parts = parts[1:score1_idx]
    team2_parts = parts[score1_idx + 1:score2_idx]
    
    team1 = ' '.join(team1_parts)
    team2 = ' '.join(team2_parts)
    
    # Normalize team names using mismatched names mapping
    team1 = normalize_team_name(team1, mismatched_names)
    team2 = normalize_team_name(team2, mismatched_names)
    
    score1 = int(parts[score1_idx])
    score2 = int(parts[score2_idx])
    
    # Get ratings
    rating_info1 = ratings_dict.get(team1)
    rating_info2 = ratings_dict.get(team2)
    
    if rating_info1 is None or rating_info2 is None:
        # Skip games where we don't have ratings for both teams
        return None
    
    rating1 = rating_info1['netRating']
    rating2 = rating_info2['netRating']
    rank1 = rating_info1['rank']
    rank2 = rating_info2['rank']
    
    # Determine which team has better rating
    if rank1 < rank2:
        higher_team = team1
        higher_rating = rating1
        higher_rank = rank1
        higher_score = score1
        lower_team = team2
        lower_rating = rating2
        lower_rank = rank2
        lower_score = score2
    else:
        higher_team = team2
        higher_rating = rating2
        higher_rank = rank2
        higher_score = score2
        lower_team = team1
        lower_rating = rating1
        lower_rank = rank1
        lower_score = score1
    
    # Determine winner
    if score1 > score2:
        winning_team = team1
    else:
        winning_team = team2
    
    return {
        "year": year,
        "date": date_str,
        "higherSeedTeam": higher_team,
        "lowerSeedTeam": lower_team,
        "higherSeedScore": higher_score,
        "lowerSeedScore": lower_score,
        "winningTeam": winning_team,
        "higherRating": higher_rating,
        "lowerRating": lower_rating,
        "higherRank": higher_rank,
        "lowerRank": lower_rank,
        "homeTeam": None if isNeutral else team2,
        "location": location if isNeutral else team2
    }

def process_year(reg_season_dir, year):
    """Process all regular season games for a given year."""
    reg_season_file = f'{reg_season_dir}/{year}.txt'
    matchups_file = f'/home/tmoran/personal/madness/src/model/matchups/{year}.json'
    
    if not os.path.exists(reg_season_file):
        print(f"Skipping {year}: No regular season file found")
        return
    
    # Load mismatched names
    mismatched_names = load_mismatched_names()
    
    # Load ratings
    ratings_dict = load_ratings(year)
    if not ratings_dict:
        print(f"Skipping {year}: No ratings found")
        return
    
    # Load existing matchups
    if os.path.exists(matchups_file):
        with open(matchups_file, 'r') as f:
            matchups = json.load(f)
    else:
        matchups = []
    
    # Parse regular season games
    new_games = []
    with open(reg_season_file, 'r') as f:
        gameCtr = 0
        for line in f:
            line = line.strip()
            if not line or line.startswith('/*') or line.startswith('*/'):
                continue
            
            game = parse_game_line(line, year, ratings_dict, mismatched_names, gameCtr)
            if game:
                new_games.append(game)
                gameCtr += 1
    
    # Append new games to matchups
    matchups.extend(new_games)
    
    # Save updated matchups
    with open(matchups_file, 'w') as f:
        json.dump(matchups, f, indent=2)
    
    print(f"Processed {year}: Added {len(new_games)} regular season games to {matchups_file}")

def delete_regular_season_games():
    """Delete all regular season games (those with higherRating field) from matchups files."""
    matchups_dir = '/home/tmoran/personal/madness/src/model/matchups'
    
    if not os.path.exists(matchups_dir):
        print(f"Directory not found: {matchups_dir}")
        return
    
    # Get all years
    years = []
    for filename in os.listdir(matchups_dir):
        if filename.endswith('.json'):
            year = filename.replace('.json', '')
            years.append(year)
    
    years.sort()
    
    for year in years:
        matchups_file = f'{matchups_dir}/{year}.json'
        
        with open(matchups_file, 'r') as f:
            matchups = json.load(f)
        
        # Filter out regular season games (those with higherRating field)
        original_count = len(matchups)
        matchups = [m for m in matchups if 'higherRating' not in m]
        deleted_count = original_count - len(matchups)
        
        # Save filtered matchups
        with open(matchups_file, 'w') as f:
            json.dump(matchups, f, indent=2)
        
        if deleted_count > 0:
            print(f"{year}: Deleted {deleted_count} regular season games")
        else:
            print(f"{year}: No regular season games found")
    
    print("\nDone deleting regular season games from all matchups files!")

def main():
    delete_regular_season_games()
    
    """Process all years with regular season game files."""
    reg_season_dir = '/home/tmoran/personal/madness/src/model/regSeasonGames'
    
    if not os.path.exists(reg_season_dir):
        print(f"Directory not found: {reg_season_dir}")
        return
    
    # Get all years from the regSeasonGames directory
    years = []
    for filename in os.listdir(reg_season_dir):
        if filename.endswith('.txt'):
            year = filename.replace('.txt', '')
            years.append(year)
    
    years.sort()
    
    for year in years:
        process_year(reg_season_dir, year)
    
    print("\nDone processing all years!")

if __name__ == "__main__":
    main()
