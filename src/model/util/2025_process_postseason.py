import json

# Team seeds from bracket
seeds = {
    # Region 1
    "Duke": 1, "Alabama": 2, "Wisconsin": 3, "Arizona": 4, "Oregon": 5, "BYU": 6, 
    "Saint Mary's": 7, "Mississippi St.": 8, "Baylor": 9, "Vanderbilt": 10, "VCU": 11, 
    "Liberty": 12, "Akron": 13, "Montana": 14, "Robert Morris": 15, "American": 16, 
    "Mount St. Mary's": 16,
    # Region 2
    "Florida": 1, "St. John's": 2, "Texas Tech": 3, "Maryland": 4, "Memphis": 5, 
    "Missouri": 6, "Kansas": 7, "Connecticut": 8, "Oklahoma": 9, "Arkansas": 10, 
    "Drake": 11, "Colorado St.": 12, "Grand Canyon": 13, "UNC Wilmington": 14, 
    "Nebraska Omaha": 15, "Norfolk St.": 16,
    # Region 3
    "Auburn": 1, "Michigan St.": 2, "Iowa St.": 3, "Texas A&M": 4, "Michigan": 5, 
    "Mississippi": 6, "Marquette": 7, "Louisville": 8, "Creighton": 9, "New Mexico": 10, 
    "San Diego St.": 11, "North Carolina": 11, "UC San Diego": 12, "Yale": 13, 
    "Lipscomb": 14, "Bryant": 15, "Alabama St.": 16, "Saint Francis": 16,
    # Region 4
    "Houston": 1, "Tennessee": 2, "Kentucky": 3, "Purdue": 4, "Clemson": 5, "Illinois": 6, 
    "UCLA": 7, "Gonzaga": 8, "Georgia": 9, "Utah St.": 10, "Texas": 11, "Xavier": 11, 
    "McNeese": 12, "High Point": 13, "Troy": 14, "Wofford": 15, "SIUE": 16
}

# Load ratings
with open('/home/tmoran/personal/madness/src/model/ratings/2025.json', 'r') as f:
    ratings_data = json.load(f)

ratings = {}
for team in ratings_data:
    ratings[team['team']] = {
        'rating': team['netRating'],
        'rank': team['rank']
    }

# Handle team name variations
team_name_mapping = {
    "Ole Miss": "Mississippi",
    "UConn": "Connecticut",
    "Omaha": "Nebraska Omaha"
}

def get_team_name(name):
    return team_name_mapping.get(name, name)

# Parse postseason games
games = []
with open('/home/tmoran/personal/madness/src/model/util/2025posteason.txt', 'r') as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        
        parts = line.split()
        date = parts[0]
        
        # Find the score positions (they're integers)
        score_positions = []
        for i, part in enumerate(parts):
            if part.isdigit():
                score_positions.append(i)
        
        if len(score_positions) < 2:
            continue
        
        # Get team names and scores
        team1_parts = parts[1:score_positions[0]]
        team1 = ' '.join(team1_parts)
        score1 = int(parts[score_positions[0]])
        
        team2_parts = parts[score_positions[0]+1:score_positions[1]]
        team2 = ' '.join(team2_parts)
        score2 = int(parts[score_positions[1]])
        
        # Get round and location (last parts after second score)
        remaining = parts[score_positions[1]+1:]
        # Round could be "NP", "1NP", etc. Location is the rest
        round_info = remaining[0] if remaining else "NP"
        location = ' '.join(remaining[1:]) if len(remaining) > 1 else ""
        
        games.append({
            'date': date,
            'team1': get_team_name(team1),
            'team2': get_team_name(team2),
            'score1': score1,
            'score2': score2,
            'round_info': round_info
        })

# Determine rounds based on dates and matchups
# First Four: March 18-19
# Round of 64: March 20-21
# Round of 32: March 22-23
# Sweet 16: March 27-28
# Elite 8: March 29-30
# Final Four: April 5
# Championship: April 7
# NIT games: April 1, 3

def get_round(date, team1, team2):
    # Check if both teams are in NCAA tournament (have seeds)
    if team1 not in seeds and team2 not in seeds:
        return None  # NIT or other non-NCAA tournament game
    
    if '03/18' in date or '03/19' in date:
        return 68  # First Four
    elif '03/20' in date or '03/21' in date:
        return 64  # Round of 64
    elif '03/22' in date or '03/23' in date:
        return 32  # Round of 32
    elif '03/27' in date or '03/28' in date:
        return 16  # Sweet 16
    elif '03/29' in date or '03/30' in date:
        return 8   # Elite 8
    elif '04/05' in date:
        return 4   # Final Four
    elif '04/07' in date:
        return 2   # Championship
    return 64

# Create matchup entries
matchup_entries = []

for game in games:
    round_num = get_round(game['date'], game['team1'], game['team2'])
    
    # Skip NIT games
    if round_num is None:
        continue
    
    team1 = game['team1']
    team2 = game['team2']
    score1 = game['score1']
    score2 = game['score2']
    
    # Get seeds (if available)
    seed1 = seeds.get(team1)
    seed2 = seeds.get(team2)
    
    # Get ratings
    rating1 = ratings.get(team1, {}).get('rating', 0)
    rank1 = ratings.get(team1, {}).get('rank', 0)
    rating2 = ratings.get(team2, {}).get('rating', 0)
    rank2 = ratings.get(team2, {}).get('rank', 0)
    
    # Determine higher/lower seed
    if seed1 and seed2:
        if seed1 < seed2:  # Lower number = higher seed
            higher_seed = seed1
            higher_seed_team = team1
            higher_seed_score = score1
            lower_seed = seed2
            lower_seed_team = team2
            lower_seed_score = score2
            higher_rating = rating1
            higher_rank = rank1
            lower_rating = rating2
            lower_rank = rank2
        else:
            higher_seed = seed2
            higher_seed_team = team2
            higher_seed_score = score2
            lower_seed = seed1
            lower_seed_team = team1
            lower_seed_score = score1
            higher_rating = rating2
            higher_rank = rank2
            lower_rating = rating1
            lower_rank = rank1
    else:
        # For games without seeds (later rounds), use rating as tiebreaker
        if rank1 < rank2:  # Lower rank = better team
            higher_seed_team = team1
            higher_seed_score = score1
            lower_seed_team = team2
            lower_seed_score = score2
            higher_rating = rating1
            higher_rank = rank1
            lower_rating = rating2
            lower_rank = rank2
            # For later rounds, seeds aren't meaningful, use None or determine from earlier games
            higher_seed = seed1 if seed1 else None
            lower_seed = seed2 if seed2 else None
        else:
            higher_seed_team = team2
            higher_seed_score = score2
            lower_seed_team = team1
            lower_seed_score = score1
            higher_rating = rating2
            higher_rank = rank2
            lower_rating = rating1
            lower_rank = rank1
            higher_seed = seed2 if seed2 else None
            lower_seed = seed1 if seed1 else None
    
    # Determine winner
    winner = team1 if score1 > score2 else team2
    
    entry = {
        "year": 2025,
        "round": round_num,
        "higherSeed": higher_seed,
        "higherSeedTeam": higher_seed_team,
        "lowerSeed": lower_seed,
        "lowerSeedTeam": lower_seed_team,
        "higherSeedScore": higher_seed_score,
        "lowerSeedScore": lower_seed_score,
        "winningTeam": winner,
        "higherRating": higher_rating,
        "lowerRating": lower_rating,
        "higherRank": higher_rank,
        "lowerRank": lower_rank
    }
    
    matchup_entries.append(entry)

# Print as JSON
print(json.dumps(matchup_entries, indent=2))
