import json

def print_detailed_stats(enhancedFile, baseFile, upper_threshold=0.05):
    """
    Print detailed upset prediction statistics broken down by postseason status.
    
    Args:
        upper_threshold: Minimum difference in upset_prob (as decimal) to consider significant.
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
        if prob_diff >= 1 + upper_threshold:
            category = 'higher'
        elif prob_diff <= 1 - upper_threshold:
            category = 'lower'
        else:
            continue  # Skip games within upper_threshold
        
        # Update postseason stats
        stats_by_postseason[is_postseason][category]['total'] += 1
        if actual_upset == 1:
            stats_by_postseason[is_postseason][category]['actual_upsets'] += 1
        else:
            stats_by_postseason[is_postseason][category]['no_upsets'] += 1
    
    # Print results
    print(f"\n{'='*70}")
    print(f"DETAILED UPSET PROBABILITY STATISTICS (upper_threshold: {upper_threshold*100:.1f}%)")
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

def test_enhanced_signal_symmetrically(enhancedFile, baseFile, bin_size=0.05, threshold=0.05):
    """
    Test whether the enhanced model provides real signal by binning games based on 
    base model probabilities and checking if enhanced model correctly discriminates
    within each bin. 
    
    It's important to note that the enhanced models are generally more upset-prone and so we have different thresholds for
    when it feels like one model is stepping out and making a statistically significant different prediction.
    
    The key insight: Within games the base model rates similarly (e.g., all 15-20% 
    upset chance), if enhanced > base by threshold, do those games upset more frequently?
    If enhanced < base by threshold, do those games upset less frequently?
    
    Args:
        bin_size: Size of probability bins (default 0.05 = 5%)
        threshold: Percentage-based threshold for significant difference (e.g., 0.05 = 5%)
    """
    # Load both result files
    with open(baseFile, 'r') as f:
        base_results = json.load(f)
    
    with open(enhancedFile, 'r') as f:
        enhanced_results = json.load(f)
    
    # Create bins from 0 to 0.5
    bins = {}
    max_prob = 0.35
    
    # Initialize bins
    current = 0
    while current < max_prob:
        bin_key = f"{current:.2f}-{current+bin_size:.2f}"
        bins[bin_key] = {
            'range': (current, current + bin_size),
            'enhanced_higher': {'total': 0, 'upsets': 0},  # enhanced > base
            'enhanced_lower': {'total': 0, 'upsets': 0}    # enhanced < base
        }
        current += bin_size
    
    # Categorize games into bins based on base model probability
    for base_game, enhanced_game in zip(base_results, enhanced_results):
        base_prob = base_game['upset_prob']
        enhanced_prob = enhanced_game['upset_prob']
        actual_upset = enhanced_game['actual_upset']
        
        # Skip division by zero
        if base_prob == 0:
            continue
        
        prob_ratio = enhanced_prob / base_prob
        
        # Find the appropriate bin
        for bin_key, bin_data in bins.items():
            if bin_data['range'][0] <= base_prob < bin_data['range'][1]:
                # Categorize by whether enhanced is significantly higher or lower than base
                if prob_ratio >= 1 + threshold:
                    bin_data['enhanced_higher']['total'] += 1
                    if actual_upset == 1:
                        bin_data['enhanced_higher']['upsets'] += 1
                elif prob_ratio <= 1 - threshold:
                    bin_data['enhanced_lower']['total'] += 1
                    if actual_upset == 1:
                        bin_data['enhanced_lower']['upsets'] += 1
                break
    
    # Print results
    print(f"\n{'='*90}")
    print(f"ENHANCED MODEL SIGNAL TEST (Bin Size: {bin_size*100:.0f}%, threshold: {threshold*100:.1f}%)")
    print(f"{'='*90}\n")
    # print("Within each base probability bin, comparing upset rates when enhanced > base vs < base:")
    # print("✓ = Enhanced model provides positive signal (higher upset rate when enh > base)\n")
    
    print(f"{'Base Bin':<12} {'Enh>Base':<10} {'Rate':<8} {'Enh<Base':<10} {'Rate':<8} {'Diff':<8} {'Signal'}")
    print(f"{'-'*68}")
    
    total_positive_signal_bins = 0
    total_bins_with_data = 0
    
    for bin_key, bin_data in sorted(bins.items()):
        higher = bin_data['enhanced_higher']
        lower = bin_data['enhanced_lower']
        
        if higher['total'] == 0 and lower['total'] == 0:
            continue
        
        total_bins_with_data += 1
        
        # Calculate upset rates
        higher_rate = (higher['upsets'] / higher['total']) if higher['total'] > 0 else 0
        lower_rate = (lower['upsets'] / lower['total']) if lower['total'] > 0 else 0
        diff = higher_rate - lower_rate
        
        # Check if enhanced provides positive signal
        has_signal = '✓' if diff > 0 and higher['total'] > 0 and lower['total'] > 0 else '✗'
        if diff > 0 and higher['total'] > 0 and lower['total'] > 0:
            total_positive_signal_bins += 1
        
        higher_str = f"{higher['total']}" if higher['total'] > 0 else "-"
        lower_str = f"{lower['total']}" if lower['total'] > 0 else "-"
        higher_rate_str = f"{higher_rate*100:>6.1f}%" if higher['total'] > 0 else "   -"
        lower_rate_str = f"{lower_rate*100:>6.1f}%" if lower['total'] > 0 else "   -"
        diff_str = f"{diff*100:>+6.1f}%" if higher['total'] > 0 and lower['total'] > 0 else "   -"
        
        print(f"{bin_key:<12} {higher_str:<10} {higher_rate_str:<8} "
              f"{lower_str:<10} {lower_rate_str:<8} {diff_str:<8} {has_signal}")
    
    # Summary statistics
    print(f"{'-'*68}")
    print(f"\nSUMMARY:")
    print(f"  Bins with positive signal: {total_positive_signal_bins}/{total_bins_with_data}")
    if total_bins_with_data > 0:
        print(f"  Percentage: {total_positive_signal_bins/total_bins_with_data*100:.1f}%")
    
    # Overall weighted difference
    total_higher_upsets = 0
    total_higher_games = 0
    total_lower_upsets = 0
    total_lower_games = 0
    
    for bin_data in bins.values():
        total_higher_upsets += bin_data['enhanced_higher']['upsets']
        total_higher_games += bin_data['enhanced_higher']['total']
        total_lower_upsets += bin_data['enhanced_lower']['upsets']
        total_lower_games += bin_data['enhanced_lower']['total']
    
    if total_higher_games > 0 and total_lower_games > 0:
        overall_higher_rate = total_higher_upsets / total_higher_games
        overall_lower_rate = total_lower_upsets / total_lower_games
        overall_diff = overall_higher_rate - overall_lower_rate
        
        print(f"\nOVERALL (across all bins):")
        print(f"  When enhanced > base: {overall_higher_rate*100:.2f}% upset rate ({total_higher_upsets}/{total_higher_games})")
        print(f"  When enhanced < base: {overall_lower_rate*100:.2f}% upset rate ({total_lower_upsets}/{total_lower_games})")
        print(f"  Difference: {overall_diff*100:+.2f} percentage points")
        print(f"\n  Interpretation: Enhanced model {'DOES' if overall_diff > 0 else 'DOES NOT'} "
              f"provide real predictive signal")
    
    print(f"\n{'='*90}\n")

def test_enhanced_signal_asymmetrically(enhancedFile, baseFile, bin_size=0.05, threshold=0.05, year=0):
    # Load both result files
    with open(baseFile, 'r') as f:
        base_results = json.load(f)
    
    with open(enhancedFile, 'r') as f:
        enhanced_results = json.load(f)
    
    # Create bins from 0 to 0.5
    bins = {}
    max_prob = 0.35
    
    # Initialize bins
    current = 0
    while current < max_prob:
        bin_key = f"{current:.2f}-{current+bin_size:.2f}"
        bins[bin_key] = {
            'range': (current, current + bin_size),
            'enhanced_higher': {'total': 0, 'upsets': 0},  # enhanced > base
            'base_average_prob': {'total': 0, 'sum_probs': 0},
            'enh_average_prob': {'total': 0, 'sum_probs': 0}
        }
        current += bin_size
    
    # Categorize games into bins based on base model probability
    for base_game, enhanced_game in zip(base_results, enhanced_results):
        if year > 0 and base_game["year"] != year:
            continue
        base_prob = base_game['upset_prob']
        enhanced_prob = enhanced_game['upset_prob']
        actual_upset = enhanced_game['actual_upset']
        
        if(base_game["year"] == 2026 and base_prob > 0.1):
            print(f"{base_game['year']} {base_game['higher_seed']}/{base_game['lower_seed']} enh prob: {round(enhanced_prob, 2)}, upset? {actual_upset}")
        
        # Skip division by zero
        if base_prob == 0:
            continue
        
        prob_ratio = enhanced_prob / base_prob
        
        # Find the appropriate bin
        for bin_key, bin_data in bins.items():
            if bin_data['range'][0] <= base_prob < bin_data['range'][1]:
                # Categorize by whether enhanced is significantly higher or lower than base
                if prob_ratio >= 1 + threshold:
                    bin_data['enhanced_higher']['total'] += 1
                    bin_data['base_average_prob']['total'] += 1
                    bin_data['base_average_prob']['sum_probs'] += base_prob
                    bin_data['enh_average_prob']['total'] += 1
                    bin_data['enh_average_prob']['sum_probs'] += enhanced_prob
                    if actual_upset == 1:
                        bin_data['enhanced_higher']['upsets'] += 1
    
    # Print results
    year_str = f" for {year}" if year > 0 else ""
    print(f"\n{'='*68}")
    print(f"ENHANCED MODEL SIGNAL TEST {year_str}  (Bin Size: {bin_size*100:.0f}%, threshold: {threshold*100:.1f}%)")
    print(f"{'='*68}\n")
    print(f"{'Base Bin':<12} {'Enh>Base':<12} {'Rate':<10} {'Base Avg':<12} {'Enh Avg':<12} {'Enh Diff':<12} {'Diff':<8} {'Signal'}")
    print(f"{'-'*68}")
    
    total_positive_signal_bins = 0
    total_bins_with_data = 0
    
    for bin_key, bin_data in sorted(bins.items()):
        higher = bin_data['enhanced_higher']
        base_averages = bin_data['base_average_prob']
        enh_averages = bin_data['enh_average_prob']
        if higher['total'] == 0:
            continue
        
        total_bins_with_data += 1
        
        # Calculate upset rates
        higher_rate = (higher['upsets'] / higher['total'])
        base_average_rate = (base_averages['sum_probs'] / base_averages['total'])
        enh_average_rate = (enh_averages['sum_probs'] / enh_averages['total'])
        diff = higher_rate - base_average_rate
        enh_diff = higher_rate - enh_average_rate
        
        # Check if enhanced provides positive signal
        has_signal = '✓' if diff > 0 else '✗'
        if diff > 0:
            total_positive_signal_bins += 1
        
        higher_str = f"{higher['total']}"
        higher_rate_str = f"{higher_rate*100:>6.1f}%"
        diff_str = f"{diff*100:>+6.1f}%"
        enh_diff_str = f"{enh_diff*100:>+6.1f}%"
        
        print(f"{bin_key:<12} {higher_str:<10} {higher_rate_str:<8} "
              f"{base_average_rate*100:>12f}% {enh_average_rate*100:>12f}% {enh_diff_str:<12} {diff_str:<12} {has_signal}")
    
    print(f"{'-'*68}")
    
    # Overall weighted difference
    total_higher_upsets = 0
    total_higher_games = 0
    total_base_probs = 0
    total_enh_probs = 0
    
    for bin_data in bins.values():
        total_higher_upsets += bin_data['enhanced_higher']['upsets']
        total_higher_games += bin_data['enhanced_higher']['total']
        total_base_probs += bin_data['base_average_prob']['sum_probs']
        total_enh_probs += bin_data['enh_average_prob']['sum_probs']
        
    if total_higher_games > 0:
        overall_higher_rate = total_higher_upsets / total_higher_games
        overall_base_rate = total_base_probs / total_higher_games
        overall_enh_rate = total_enh_probs / total_higher_games
        overall_diff = overall_higher_rate - overall_base_rate
        overall_enh_diff = overall_enh_rate - overall_higher_rate
        
        print(f"\nOVERALL (across all bins):")
        print(f"  When enhanced > base: {overall_higher_rate*100:.2f}% upset rate ({total_higher_upsets}/{total_higher_games})")
        print(f"  Avg based guessed rate: {overall_base_rate*100:.2f}% upset rate ({round(total_base_probs)}/{total_higher_games})")
        print(f"  Avg enhanced guessed rate: {overall_enh_rate*100:.2f}% upset rate ({round(total_enh_probs)}/{total_higher_games})")
        print(f"  Difference: {overall_diff*100:+.2f} percentage points")
        print(f"  Enhanced Difference: {overall_enh_diff*100:+.2f} percentage points")
        

if __name__ == "__main__":
    test_enhanced_signal_asymmetrically(enhancedFile='outputs/13to26lr_3PLoThreeTo.json', 
        baseFile='outputs/13to26lr_base.json', bin_size=0.05, threshold=0.07)#, year=2026)