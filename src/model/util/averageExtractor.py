import json
import os
from pathlib import Path

HOME_COURT_ADVANTAGE = 4.29

def count_upsets_by_year():
    """Count upsets for each year based on rating differentials >= 6."""
    base_path = Path(__file__).parent.parent
    matchups_dir = base_path / 'matchups'
    
    # Get all years from matchups directory
    years = sorted([f.stem for f in matchups_dir.glob('*.json')])
    
    upset_data = {}
    
    for year in years:
        matchups_file = matchups_dir / f'{year}.json'
        
        with open(matchups_file, 'r') as f:
            matchups = json.load(f)
        
        upsets = 0
        total_chances = 0
        
        for matchup in matchups:
            # Get base ratings
            higher_rating = matchup.get('higherRating')
            lower_rating = matchup.get('lowerRating')
            home_team = matchup.get('homeTeam')
            higher_seed_team = matchup.get('higherSeedTeam')
            winning_team = matchup.get('winningTeam')
            lower_seed_team = matchup.get('lowerSeedTeam')
            
            # Skip if missing required data
            if higher_rating is None or lower_rating is None:
                continue
            
            # Apply home court advantage adjustments
            adjusted_higher = higher_rating
            adjusted_lower = lower_rating
            
            if home_team and home_team != "null" and home_team != "":
                if higher_seed_team == home_team:
                    adjusted_higher += HOME_COURT_ADVANTAGE
                    adjusted_lower -= HOME_COURT_ADVANTAGE
                else:
                    adjusted_higher -= HOME_COURT_ADVANTAGE
                    adjusted_lower += HOME_COURT_ADVANTAGE
            
            # Calculate rating differential
            rating_diff = adjusted_higher - adjusted_lower
            
            # Count games where upset was possible (rating diff >= 6)
            if rating_diff >= 6:
                total_chances += 1
                # Count actual upsets (lower seed won)
                if winning_team == lower_seed_team:
                    upsets += 1
        
        # Calculate percentage
        upset_pct = (upsets / total_chances * 100) if total_chances > 0 else 0
        
        upset_data[year] = {
            "upsets": upsets,
            "total_chances": total_chances,
            "upset_percentage": round(upset_pct, 2)
        }
    
    # Save to JSON file
    output_file = base_path / 'upsets_by_year.json'
    with open(output_file, 'w') as f:
        json.dump(upset_data, f, indent=2)
    
    print(f"Upset counts saved to {output_file}")
    print(f"\nUpset statistics by year:")
    for year, data in upset_data.items():
        print(f"  {year}: {data['upsets']}/{data['total_chances']} ({data['upset_percentage']}%)")
    
    return upset_data

def compute_year_averages(year):
    """Compute averages for a given year from misc and fourFactors data."""
    base_path = Path(__file__).parent.parent
    misc_file = base_path / 'misc' / f'{year}.json'
    ff_file = base_path / 'fourFactors' / f'{year}.json'
    
    # Check if both files exist
    if not misc_file.exists() or not ff_file.exists():
        return None
    
    # Load data
    with open(misc_file, 'r') as f:
        misc_data = json.load(f)
    
    with open(ff_file, 'r') as f:
        ff_data = json.load(f)
    
    # Compute averages for misc stats
    misc_stats = ['3P_pct', '2P_pct', 'FT_pct', 'Blk_pct', 'Stl_pct', 'A_pct', '3PA_pct']
    misc_averages = {}
    
    for stat in misc_stats:
        values = [float(team[stat]) for team in misc_data if stat in team and team[stat]]
        if values:
            misc_averages[stat] = round(sum(values) / len(values), 2)
    
    # Compute averages for fourFactors stats
    ff_stats = ['adjTempo', 'adjOE', 'adjDE', 'eFG_pct_off', 'TO_pct_off', 'OR_pct_off', 'FTRate_off']
    ff_averages = {}
    
    for stat in ff_stats:
        values = [float(team[stat]) for team in ff_data if stat in team and team[stat]]
        if values:
            ff_averages[stat] = round(sum(values) / len(values), 2)
    
    # Combine averages
    year_averages = {
        'year': year,
        **misc_averages,
        **ff_averages
    }
    
    return year_averages

def main():
    """Process all years and create average files."""
    base_path = Path(__file__).parent.parent
    misc_dir = base_path / 'misc'
    output_dir = base_path / 'averages'
    
    # Create output directory if it doesn't exist
    output_dir.mkdir(exist_ok=True)
    
    # Get all years from misc directory
    # years = sorted([f.stem for f in misc_dir.glob('*.json')])
    years = [2026]  # --- IGNORE ---
    
    print(f"Processing {len(years)} years...")
    
    for year in years:
        averages = compute_year_averages(year)
        
        if averages:
            output_file = output_dir / f'{year}.json'
            with open(output_file, 'w') as f:
                json.dump(averages, f, indent=2)
            print(f"Created {year}.json with {len(averages) - 1} stats")
        else:
            print(f"Skipped {year} - missing data")
    
    print(f"\nDone! Output files saved to {output_dir}")

if __name__ == '__main__':
    main()
