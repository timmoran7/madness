import json
import glob
import pandas as pd
import numpy as np
import math

from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import brier_score_loss
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import log_loss

START_YEAR = 2015
SPLIT_YEAR = 2021

# seed diffs straight from 97-24 data, less common diffs (even) 
# just the average of above and below diffs since small sample
roughSeedUpsetProbs = {
    5: 0.379,
    6: 0.346,
    7: 0.314,
    8: 0.263,
    9: 0.213,
    10: 0.195,
    11: 0.109,
    12: 0.096,
    13: 0.083,
    14: 0.051,
    15: 0.019
}

HOME_COURT_ADVANTAGE = 4.29 # 3-point HCA PPG / 70 possessions per game * 100 possessions

def calculate_avg_seed_upset_probs():  
    avgSeedUpsetProbs = {}  
    seed_diff_stats = {}  # {seed_diff: {"total": count, "upsets": count}}
    
    fullRange = [year for year in range(START_YEAR, 2025) if year != 2020]
    for year in fullRange:
        matchups = load_json(f"matchups/{year}.json")
        
        for matchup in matchups:
            if matchup["round"] >= 16:  # Only consider games before Sweet Sixteen
                seed_diff = matchup["lowerSeed"] - matchup["higherSeed"]
                
                # Initialize if not seen before
                if seed_diff not in seed_diff_stats:
                    seed_diff_stats[seed_diff] = {"total": 0, "upsets": 0}
                
                # Count total games
                seed_diff_stats[seed_diff]["total"] += 1
                
                # Count upsets (when lower seed wins)
                if matchup["winningTeam"] == matchup["lowerSeedTeam"]:
                    seed_diff_stats[seed_diff]["upsets"] += 1
    
    # Calculate probabilities
    for seed_diff, stats in seed_diff_stats.items():
        avgSeedUpsetProbs[seed_diff] = stats["upsets"] / stats["total"]
    return dict(sorted(avgSeedUpsetProbs.items()))

def load_json(path):
    with open(path, "r") as f:
        return json.load(f)
    
def build_team_stats(misc, four_factors):
    misc_df = pd.DataFrame(misc)
    ff_df = pd.DataFrame(four_factors)

    df = misc_df.merge(ff_df, on="team", how="inner")
    
    # Convert numeric columns
    for col in df.columns:
        if col != "team" and col != "conf":
            df[col] = pd.to_numeric(df[col], errors="coerce")

    colsToIgnore = ["conf", "Stl_pct", "Blk_pct", "2P_pct", "OR_pct_def",
        "eFG_pct_off", "eFG_pct_def", "FTRate_off", "2P_Dist"]
    return df.set_index("team").drop(columns=colsToIgnore, errors="ignore")

def build_matchup_rows(matchups, team_stats, ratingSegment, numBuckets):
    rows = []
    
    # higherSeedTeam, higherRating
    relevantMatchups = []

    for m in matchups: 
        adjustedHigherRating, adjustedLowerRating = m["higherRating"], m["lowerRating"]
        if "homeTeam" not in m or m["homeTeam"] == "null" or m["homeTeam"] == "" or m["homeTeam"] is None:
            pass
        elif(m["higherSeedTeam"] == m["homeTeam"]):
            adjustedHigherRating += HOME_COURT_ADVANTAGE
            adjustedLowerRating -= HOME_COURT_ADVANTAGE
        else:
            adjustedHigherRating -= HOME_COURT_ADVANTAGE
            adjustedLowerRating += HOME_COURT_ADVANTAGE
        
        if(adjustedHigherRating is None or adjustedLowerRating is None):
            print("nan rating detected!")
            return []
        ratingDiff = adjustedHigherRating - adjustedLowerRating
        
        # skip if outside rating segment
        if(ratingDiff < ratingSegment[0] or ratingDiff > ratingSegment[1]):
            continue

        # optionally create buckets (pass ratingSegment max of 29.99 instead of 30 to avoid one extra bucket for ratings of exactly 30)
        if(numBuckets > 0):
            ratingRange = ratingSegment[1] - ratingSegment[0]
            bucketWidth = ratingRange / numBuckets
            m["bucket"] = ((ratingDiff - ratingSegment[0]) // bucketWidth) + 1
        else:
            m["adjustedHigherRating"] = adjustedHigherRating
            m["adjustedLowerRating"] = adjustedLowerRating
        
        relevantMatchups.append(m)
            
    rowCtr = 0
    for matchup in relevantMatchups:
        is_postseason = "round" in matchup
        hi = matchup["higherSeedTeam"]
        lo = matchup["lowerSeedTeam"]

        if hi not in team_stats.index or lo not in team_stats.index:
            continue

        hi_stats = team_stats.loc[hi]
        lo_stats = team_stats.loc[lo]

        row = {}

        noDeltaCols = ["3PA_pct", "3P_pct", "TO_pct_off", "TO_pct_def"]
        addTogetherCols = ["3PA_pct"]
        pairsWithName = [["TO_pct_off", "TO_pct_def", "TO_freq"]]
        # Stat deltas (lower seed − higher seed)
        for col in team_stats.columns:
            if(col in addTogetherCols):
                row[f"sum_{col}"] = lo_stats[col] + hi_stats[col]
            elif any(col in pair for pair in pairsWithName):
                # find the pair
                for pair in pairsWithName:
                    if col in pair:
                        other_col = pair[1] if pair[0] == col else pair[0]
                        row[f"{pair[2]}"] = hi_stats[col] + lo_stats[other_col]
                        break
                
            if(col not in noDeltaCols):
                row[f"delta_{col}"] = lo_stats[col] - hi_stats[col]
            else:
                row[f"{col}_hi"] = hi_stats[col]
                row[f"{col}_lo"] = lo_stats[col]

        # Target: upset?
        row["upset"] = int(matchup["winningTeam"] == lo)
        
        # metadata for visibility
        row["hiTeam"] = hi
        row["loTeam"] = lo
        row["year"] = matchup["year"]
        row["is_postseason"] = is_postseason
        if("lowerSeed" in matchup):
            row["seed_diff"] = matchup["lowerSeed"] - matchup["higherSeed"]
            
        if(numBuckets > 0):
            row["bucket"] = matchup["bucket"]
        else:
            row["higherRating"] = matchup["adjustedHigherRating"]
            row["lowerRating"] = matchup["adjustedLowerRating"]
            row["rating_diff"] = matchup["adjustedHigherRating"] - matchup["adjustedLowerRating"]
        rows.append(row)
        rowCtr += 1

    return rows

all_rows = []

def buildAndRunModel(
    ratingSegment = [0,50],
    colsToKeep=[],
    numBuckets=0
):
    fullRange = [year for year in range(START_YEAR, 2025) if year != 2020]
    for year in fullRange:
        misc = load_json(f"misc/{year}.json")
        ff = load_json(f"fourFactors/{year}.json")
        matchups = load_json(f"matchups/{year}.json")

        team_stats = build_team_stats(misc, ff)
        rows = build_matchup_rows(matchups, team_stats, ratingSegment, numBuckets)
        all_rows.extend(rows)

    df = pd.DataFrame(all_rows)
    
    # Keep seed_diff separate since it's only present for postseason games
    seed_diff_col = df["seed_diff"].copy() if "seed_diff" in df.columns else None
    
    # Drop seed_diff before dropna so we don't lose regular season games
    if "seed_diff" in df.columns:
        df = df.drop(columns=["seed_diff"])
    
    df = df.dropna()

    # Keep team names and metadata separate before splitting + remove favorite 3P%
    ratingDiffIdentifier = "rating_diff" if numBuckets == 0 else "bucket"
    team_info = df[["hiTeam", "loTeam", "year", "is_postseason", ratingDiffIdentifier]].copy()
    team_info["year"] = pd.to_numeric(team_info["year"])
    
    # Re-attach seed_diff to team_info (will be NaN for regular season)
    if seed_diff_col is not None:
        team_info["seed_diff"] = seed_diff_col.loc[df.index]
    
    X = df[colsToKeep].copy()
    y = df["upset"].copy()
    
    print(X.columns)
    print(X.iloc[0])
    # Train on all data before SPLIT_YEAR, test on SPLIT_YEAR and after
    # This includes both regular season and postseason games in both sets
    train_mask = team_info["year"] <= SPLIT_YEAR
    test_mask = team_info["year"] > SPLIT_YEAR

    X_train = X[train_mask]
    X_test = X[test_mask]
    y_train = y[train_mask]
    y_test = y[test_mask]

    # Scale all numeric features
    scaler = StandardScaler()
    X_train = pd.DataFrame(
        scaler.fit_transform(X_train),
        columns=X_train.columns,
        index=X_train.index
    )
    X_test = pd.DataFrame(
        scaler.transform(X_test),
        columns=X_test.columns,
        index=X_test.index
    )

    lr = LogisticRegression(
        class_weight="balanced",
        random_state=42,
        max_iter=1000,
        solver="lbfgs",
        penalty="l2",
        C=0.5   # try grid: [0.1, 0.3, 0.5, 1, 3]
    )

    lr.fit(X_train, y_train)

    # Calibrate probabilities (critical)
    calibrated_lr = CalibratedClassifierCV(
        lr, method="isotonic", cv=5
    )
    calibrated_lr.fit(X_train, y_train)

    # Evaluate
    probs = calibrated_lr.predict_proba(X_test)[:, 1]

    brier = brier_score_loss(y_test, probs)
    ll_base = log_loss(y_test, probs)
    print(f"\nBrier score: {brier:.4f}")
    print(f"Log loss: {ll_base:.4f}")

    # Build results dataframe for visibility
    test_info = team_info.loc[X_test.index]
    results = pd.DataFrame({
        "higher_seed": test_info["hiTeam"].values,
        "lower_seed": test_info["loTeam"].values,
        "year": test_info["year"].values,
        "is_postseason": test_info["is_postseason"].values,
        ratingDiffIdentifier: test_info[ratingDiffIdentifier].values,
        "actual_upset": y_test.values,
        "upset_prob": probs
    })
    
    # Add baseline seed-based upset probability for comparison (only for postseason)
    #results["seed_prob"] = results["seed_diff"].map(roughSeedUpsetProbs)
    
    return results

#'''
# Sort by upset probability (descending) to see top upset picks
results = buildAndRunModel([8,24], ["higherRating", "lowerRating", "sum_3PA_pct"], 0)
#results.to_json("logisticThreeAndTo.json", orient="records", indent=2)

#results = results.sort_values("upset_prob", ascending=False)

def print_results_summary(results):
    print("\n=== Top 20 Upset Predictions ===")
    print(results.head(20).to_string(index=False))

    print("\n=== Actual Upsets (sorted by model confidence) ===")
    actual_upsets = results[results["actual_upset"] == 1].copy()
    print(actual_upsets.head(40).to_string(index=False))

    print(f"\n=== Model captured {len(actual_upsets)} upsets in test set ===")
    print(f"Average upset probability for actual upsets: {actual_upsets['upset_prob'].mean():.3f}")
    print(f"Average upset probability for non-upsets: {results[results['actual_upset'] == 0]['upset_prob'].mean():.3f}")
    #'''

def print_model_efficacy(results):
    print("\n=== Model Efficacy Analysis (Postseason Games Only) ===")
    print("Comparing model predictions to baseline seed differential probabilities\n")
    
    # Filter to only postseason games (which have seed_diff)
    postseason_results = results[results["is_postseason"] == True].copy()
    
    # Track overall statistics
    total_higher_upsets = 0
    total_higher_games = 0
    total_lower_upsets = 0
    total_lower_games = 0
    
    for seed_diff in sorted(postseason_results["seed_diff"].unique()):
        seed_data = postseason_results[postseason_results["seed_diff"] == seed_diff]
        baseline_prob = seed_data["seed_prob"].iloc[0] if len(seed_data) > 0 else None
        
        if baseline_prob is None:
            continue
            
        # Games where model predicts higher upset probability than baseline
        model_higher = seed_data[seed_data["upset_prob"] > seed_data["seed_prob"]]
        # Games where model predicts lower upset probability than baseline
        model_lower = seed_data[seed_data["upset_prob"] < seed_data["seed_prob"]]
        
        higher_upsets = model_higher["actual_upset"].sum() if len(model_higher) > 0 else 0
        higher_total = len(model_higher)
        
        lower_upsets = model_lower["actual_upset"].sum() if len(model_lower) > 0 else 0
        lower_total = len(model_lower)
        
        # Accumulate overall stats
        total_higher_upsets += higher_upsets
        total_higher_games += higher_total
        total_lower_upsets += lower_upsets
        total_lower_games += lower_total
        
        print(f"Seed Diff {seed_diff} (Baseline Upset Prob: {baseline_prob:.3f}):")
        if higher_total > 0:
            print(f"  Model > Baseline: {higher_upsets}/{higher_total} upsets ({higher_upsets/higher_total:.3f})")
        else:
            print(f"  Model > Baseline: 0/0 upsets (N/A)")
        
        if lower_total > 0:
            print(f"  Model < Baseline: {lower_upsets}/{lower_total} upsets ({lower_upsets/lower_total:.3f})")
        else:
            print(f"  Model < Baseline: 0/0 upsets (N/A)")
        print()
    
    # Print overall summary
    print("=== OVERALL SUMMARY ===")
    if total_higher_games > 0:
        higher_pct = (total_higher_upsets / total_higher_games) * 100
        print(f"ABOVE: {total_higher_upsets}/{total_higher_games} ({higher_pct:.1f}%) GAMES W/ HIGHER PROB WERE UPSETS")
    else:
        print("ABOVE: 0/0 (N/A) GAMES W/ HIGHER PROB WERE UPSETS")
    
    if total_lower_games > 0:
        lower_pct = (total_lower_upsets / total_lower_games) * 100
        print(f"BELOW: {total_lower_upsets}/{total_lower_games} ({lower_pct:.1f}%) GAMES W/ LOWER PROB WERE UPSETS")
    else:
        print("BELOW: 0/0 (N/A) GAMES W/ LOWER PROB WERE UPSETS")

#upsetProbs = calculate_avg_seed_upset_probs()
#print(upsetProbs)
#print_model_efficacy(results)
#print_results_summary(results)