import json

def compare_upset_predictions(enhancedFile='logisticThreeAndTo.json', baseFile='logisticBase.json', threshold=0.05):
    """
    Compare enhanced model upset predictions against base model.
    
    Args:
        threshold: Minimum difference in upset_prob (as decimal) to consider significant.
                   E.g., 0.05 = 5% difference required
    """
    # Load both result files
    with open(baseFile, 'r') as f:
        base_results = json.load(f)
    
    with open(enhancedFile, 'r') as f:
        enhanced_results = json.load(f)
    
    # Track statistics
    higher_upset_prob = {
        'total': 0,
        'actual_upsets': 0,
        'no_upsets': 0
    }
    
    lower_upset_prob = {
        'total': 0,
        'actual_upsets': 0,
        'no_upsets': 0
    }
    
    # Compare each game (they're in the same order)
    for base_game, enhanced_game in zip(base_results, enhanced_results):
        base_prob = base_game['upset_prob']
        enhanced_prob = enhanced_game['upset_prob']
        actual_upset = enhanced_game['actual_upset']
        
        # not subtraction but division of probabilities
        if(base_prob == 0):
            continue
        prob_diff = enhanced_prob / base_prob
        
        # Check if enhanced has significantly higher upset probability
        if prob_diff >= 1 + threshold:
            higher_upset_prob['total'] += 1
            if actual_upset == 1:
                higher_upset_prob['actual_upsets'] += 1
            else:
                higher_upset_prob['no_upsets'] += 1
        
        # Check if enhanced has significantly lower upset probability
        elif prob_diff <= 1 - threshold:
            lower_upset_prob['total'] += 1
            if actual_upset == 1:
                lower_upset_prob['actual_upsets'] += 1
            else:
                lower_upset_prob['no_upsets'] += 1
    
    # Print results
    print(f"\n{'='*70}")
    print(f"UPSET PROBABILITY COMPARISON (Threshold: {threshold*100:.1f}%)")
    print(f"{'='*70}\n")
    
    print(f"WHEN enhanced MODEL HAS HIGHER UPSET PROBABILITY:")
    print(f"  Total games: {higher_upset_prob['total']}")
    if higher_upset_prob['total'] > 0:
        print(f"  Actual upsets: {higher_upset_prob['actual_upsets']}")
        print(f"  No upset: {higher_upset_prob['no_upsets']}")
        upset_rate = (higher_upset_prob['actual_upsets'] / higher_upset_prob['total']) * 100
        print(f"  Upset rate: {upset_rate:.2f}%")
    print()
    
    print(f"WHEN enhanced MODEL HAS LOWER UPSET PROBABILITY:")
    print(f"  Total games: {lower_upset_prob['total']}")
    if lower_upset_prob['total'] > 0:
        print(f"  Actual upsets: {lower_upset_prob['actual_upsets']}")
        print(f"  No upset: {lower_upset_prob['no_upsets']}")
        upset_rate = (lower_upset_prob['actual_upsets'] / lower_upset_prob['total']) * 100
        print(f"  Upset rate: {upset_rate:.2f}%")
    print()
    
    # Calculate overall upset rate for context
    total_games = len(base_results)
    total_upsets = sum(1 for game in enhanced_results if game['actual_upset'] == 1)
    overall_upset_rate = (total_upsets / total_games) * 100
    print(f"OVERALL DATASET:")
    print(f"  Total games: {total_games}")
    print(f"  Total upsets: {total_upsets}")
    print(f"  Overall upset rate: {overall_upset_rate:.2f}%")
    print(f"\n{'='*70}\n")


def print_detailed_stats(enhancedFile='sixenhancedResults.json', baseFile='slimmerBaseResults.json', threshold=0.05):
    """
    Print detailed upset prediction statistics broken down by enhanced and postseason status.
    
    Args:
        threshold: Minimum difference in upset_prob (as decimal) to consider significant.
    """
    # Load both result files
    with open(baseFile, 'r') as f:
        base_results = json.load(f)
    
    with open(enhancedFile, 'r') as f:
        enhanced_results = json.load(f)
    
    # Track statistics by postseason status
    stats_by_postseason = {
        True: {'higher': {'total': 0, 'actual_upsets': 0, 'no_upsets': 0},
               'lower': {'total': 0, 'actual_upsets': 0, 'no_upsets': 0}},
        False: {'higher': {'total': 0, 'actual_upsets': 0, 'no_upsets': 0},
                'lower': {'total': 0, 'actual_upsets': 0, 'no_upsets': 0}}
    }
    
    # Compare each game
    for base_game, enhanced_game in zip(base_results, enhanced_results):
        base_prob = base_game['upset_prob']
        enhanced_prob = enhanced_game['upset_prob']
        actual_upset = enhanced_game['actual_upset']
        is_postseason = enhanced_game.get('is_postseason', False)
        
        # Calculate probability difference
        if(base_prob == 0):
            continue
        prob_diff = enhanced_prob / base_prob
        
        # Classify as higher or lower upset probability
        if prob_diff >= 1 + threshold:
            category = 'higher'
        elif prob_diff <= 1 - threshold:
            category = 'lower'
        else:
            continue  # Skip games within threshold
        
        # Update postseason stats
        stats_by_postseason[is_postseason][category]['total'] += 1
        if actual_upset == 1:
            stats_by_postseason[is_postseason][category]['actual_upsets'] += 1
        else:
            stats_by_postseason[is_postseason][category]['no_upsets'] += 1
    
    # Print results
    print(f"\n{'='*70}")
    print(f"DETAILED UPSET PROBABILITY STATISTICS (Threshold: {threshold*100:.1f}%)")
    print(f"{'='*70}\n")
    
    # Print by postseason status
    print(f"\n{'-'*70}")
    print("\nBREAKDOWN BY POSTSEASON STATUS:")
    print(f"{'-'*70}")
    
    for is_postseason, label in [(True, 'Postseason')]:
        print(f"\n{label}:")
        
        higher = stats_by_postseason[is_postseason]['higher']
        print(f"  Higher upset probability than base:")
        print(f"    Total games: {higher['total']}")
        if higher['total'] > 0:
            print(f"    Actual upsets: {higher['actual_upsets']}")
            print(f"    No upset: {higher['no_upsets']}")
            upset_rate = (higher['actual_upsets'] / higher['total']) * 100
            print(f"    Upset rate: {upset_rate:.2f}%")
        
        lower = stats_by_postseason[is_postseason]['lower']
        print(f"  Lower upset probability than base:")
        print(f"    Total games: {lower['total']}")
        if lower['total'] > 0:
            print(f"    Actual upsets: {lower['actual_upsets']}")
            print(f"    No upset: {lower['no_upsets']}")
            upset_rate = (lower['actual_upsets'] / lower['total']) * 100
            print(f"    Upset rate: {upset_rate:.2f}%")
    
    print(f"\n{'='*70}\n")


if __name__ == "__main__":
    compare_upset_predictions(enhancedFile='logisticThreeAndTo.json', baseFile='logisticBase.json', threshold=0.14)
    #print_detailed_stats('fourenhancedResults.json', threshold=0.3)