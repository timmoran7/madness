import json
import os
from pathlib import Path

def calculate_net_ratings(year):
    """
    Calculate net ratings for a given year's four factors data.
    Net Rating = adjOE - adjDE
    """
    # Define paths
    four_factors_path = Path(__file__).parent.parent / "fourFactors" / f"{year}.json"
    ratings_path = Path(__file__).parent.parent / "ratings" / f"{year}.json"
    
    # Check if source file exists
    if not four_factors_path.exists():
        print(f"Warning: Four factors file for {year} not found")
        return
    
    # Read four factors data
    with open(str(four_factors_path), 'r') as f:
        four_factors = json.load(f)
    
    # Calculate net ratings
    teams_with_ratings = []
    for team_data in four_factors:
        team_name = team_data['team']
        adj_oe = float(team_data['adjOE'])
        adj_de = float(team_data['adjDE'])
        net_rating = adj_oe - adj_de
        
        teams_with_ratings.append({
            'team': team_name,
            'netRating': round(net_rating, 2)
        })
    
    # Sort by net rating (descending - higher is better)
    teams_with_ratings.sort(key=lambda x: x['netRating'], reverse=True)
    
    # Add ranks
    for rank, team in enumerate(teams_with_ratings, start=1):
        team['rank'] = rank
    
    # Write to output file
    with open(str(ratings_path), 'w') as f:
        json.dump(teams_with_ratings, f, indent=2)
    
    print(f"Created ratings file for {year} with {len(teams_with_ratings)} teams")

def add_ratings_to_postseason_games():
    """
    Add team ratings to postseason games in matchups files.
    Updates the first 63 entries in each matchups file (2010-2024, excluding 2020)
    with higherRating and lowerRating fields based on the teams' net ratings.
    """
    matchups_dir = Path(__file__).parent.parent / "matchups"
    ratings_dir = Path(__file__).parent.parent / "ratings"
    
    # Years to process (excluding 2020)
    years = [str(year) for year in range(2010, 2025) if year != 2020]
    
    for year in years:
        matchups_path = matchups_dir / f"{year}.json"
        ratings_path = ratings_dir / f"{year}.json"
        
        # Check if both files exist
        if not matchups_path.exists():
            print(f"Warning: Matchups file for {year} not found")
            continue
        if not ratings_path.exists():
            print(f"Warning: Ratings file for {year} not found")
            continue
        
        # Read ratings data
        with open(ratings_path, 'r') as f:
            ratings_data = json.load(f)
        
        # Create a lookup dictionary for team ratings
        team_ratings = {team['team']: team['netRating'] for team in ratings_data}
        
        # Read matchups data
        with open(matchups_path, 'r') as f:
            matchups_data = json.load(f)
        
        # Update first 63 entries (postseason games)
        updated_count = 0
        for i in range(min(63, len(matchups_data))):
            game = matchups_data[i]
            
            higher_team = game.get('higherSeedTeam')
            lower_team = game.get('lowerSeedTeam')
            
            # Add ratings if teams are found
            if higher_team in team_ratings:
                game['higherRating'] = team_ratings[higher_team]
                updated_count += 1
            else:
                print(f"Warning: Team '{higher_team}' not found in {year} ratings")
            
            if lower_team in team_ratings:
                game['lowerRating'] = team_ratings[lower_team]
            else:
                print(f"Warning: Team '{lower_team}' not found in {year} ratings")
        
        # Write updated data back to file
        with open(matchups_path, 'w') as f:
            json.dump(matchups_data, f, indent=2)
        
        print(f"Updated {year}: Added ratings to {updated_count} postseason games")
    
    print(f"\nCompleted! Updated matchups files from {years[0]} to {years[-1]}")

def main():
    # add ratings
    # add_ratings_to_postseason_games()
    
    #############################################
    """Process all four factors files in the fourFactors directory"""
    '''
    four_factors_dir = Path(__file__).parent / "fourFactors"
    
    # Get all year files
    years = []
    for file in four_factors_dir.glob("*.json"):
        year = file.stem  # Get filename without extension
        years.append(year)
    '''
    # Sort years
    #years.sort()
    years = [2026]
    
    print(f"Processing {len(years)} years: {min(years)} - {max(years)}")
    
    # Process each year
    for year in years:
        calculate_net_ratings(year)
    
    print(f"\nCompleted! All rating files saved to ratings/ directory")

if __name__ == "__main__":
    main()
