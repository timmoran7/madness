import json
import glob
import pandas as pd
import numpy as np

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import brier_score_loss

# first round seed diffs straight from 08-24 data, less common diffs (even) 
# just the average of above and below first-round diffs since small sample
roughSeedUpsetProbs = {
    5: 0.429,
    6: 0.385,
    7: 0.34,
    8: 0.289,
    9: 0.238,
    10: 0.195,
    11: 0.113,
    12: 0.111,
    13: 0.109,
    14: 0.07,
    15: 0.031
}
def calculate_avg_seed_upset_probs():  
    avgSeedUpsetProbs = {}  
    seed_diff_stats = {}  # {seed_diff: {"total": count, "upsets": count}}
    
    fullRange = [year for year in range(2008, 2025) if year != 2020]
    for year in fullRange:
        matchups = load_json(f"matchups/{year}.json")
        
        for matchup in matchups:
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

    colsToIgnore = ["conf", "Stl_pct", "Blk_pct", "2P_pct", "eFG_pct_off", "eFG_pct_def", "FTRate_off", "2P_Dist"]
    return df.set_index("team").drop(columns=colsToIgnore, errors="ignore")

def build_matchup_rows(matchups, team_stats):
    rows = []

    #filter out non-upset games + post-sweet-sixteen games
    relevantMatchups = [m for m in matchups if m["lowerSeed"] - m["higherSeed"] > 4 and m["round"] >= 16]
    for matchup in relevantMatchups:
        hi = matchup["higherSeedTeam"]
        lo = matchup["lowerSeedTeam"]

        if hi not in team_stats.index or lo not in team_stats.index:
            continue

        hi_stats = team_stats.loc[hi]
        lo_stats = team_stats.loc[lo]

        row = {}

        noDeltaCols = ["3PA_pct", "3P_pct"]
        # Stat deltas (lower seed − higher seed)
        for col in team_stats.columns:
            if(col not in noDeltaCols):
                row[f"delta_{col}"] = lo_stats[col] - hi_stats[col]
            else:
                row[f"{col}_hi"] = hi_stats[col]
                row[f"{col}_lo"] = lo_stats[col]

        # Seed gap (still useful context)
        row["seed_diff"] = matchup["lowerSeed"] - matchup["higherSeed"]

        # Target: upset?
        row["upset"] = int(matchup["winningTeam"] == lo)
        
        # metadata for visibility
        row["hiTeam"] = hi
        row["loTeam"] = lo
        row["year"] = matchup["year"]
        row["hiSeed"] = matchup["higherSeed"]
        row["loSeed"] = matchup["lowerSeed"]

        rows.append(row)

    return rows

all_rows = []

def buildAndRunModel():
    # 2008-2024
    fullRange = [year for year in range(2008, 2025) if year != 2020]
    for year in fullRange:
        misc = load_json(f"misc/{year}.json")
        ff = load_json(f"fourFactors/{year}.json")
        matchups = load_json(f"matchups/{year}.json")

        team_stats = build_team_stats(misc, ff)
        rows = build_matchup_rows(matchups, team_stats)
        all_rows.extend(rows)

    df = pd.DataFrame(all_rows).dropna()

    # Keep team names separate before splitting
    team_info = df[["hiTeam", "loTeam", "year", "hiSeed", "loSeed"]].copy()
    X = df.drop(columns=["upset", "hiTeam", "loTeam", "year", "hiSeed", "loSeed"])
    y = df["upset"]

    # Split by year: train on 2008-2021, test on 2022+
    train_mask = df["year"] < 2020
    test_mask = df["year"] > 2020

    X_train = X[train_mask]
    X_test = X[test_mask]
    y_train = y[train_mask]
    y_test = y[test_mask]

    rf = RandomForestClassifier(
        n_estimators=600,
        max_depth=5,
        min_samples_leaf=20,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1
    )

    rf.fit(X_train, y_train)

    # Calibrate probabilities (critical)
    calibrated_rf = CalibratedClassifierCV(
        rf, method="isotonic", cv=5
    )
    calibrated_rf.fit(X_train, y_train)

    # Evaluate
    probs = calibrated_rf.predict_proba(X_test)[:, 1]

    brier = brier_score_loss(y_test, probs)
    print(f"\nBrier score: {brier:.4f}")

    # Build results dataframe for visibility
    results = pd.DataFrame({
        "higher_seed": team_info.loc[X_test.index, "hiTeam"].values,
        "lower_seed": team_info.loc[X_test.index, "loTeam"].values,
        "year": team_info.loc[X_test.index, "year"].values,
        "hi seed": team_info.loc[X_test.index, "hiSeed"].values,
        "lo seed": team_info.loc[X_test.index, "loSeed"].values,
        "actual_upset": y_test.values,
        "upset_prob": probs
    })
    
    # Add baseline seed differential probability
    results["seed_diff"] = results["lo seed"] - results["hi seed"]
    results["seed_prob"] = results["seed_diff"].map(roughSeedUpsetProbs)
    
    return results

#'''
# Sort by upset probability (descending) to see top upset picks
results = buildAndRunModel()
results = results.sort_values("upset_prob", ascending=False)

def print_results_summary(results):
    print("\n=== Top 20 Upset Predictions ===")
    print(results.head(20).to_string(index=False))

    print("\n=== Actual Upsets (sorted by model confidence) ===")
    actual_upsets = results[results["actual_upset"] == 1].copy()
    print(actual_upsets.to_string(index=False))

    print(f"\n=== Model captured {len(actual_upsets)} upsets in test set ===")
    print(f"Average upset probability for actual upsets: {actual_upsets['upset_prob'].mean():.3f}")
    print(f"Average upset probability for non-upsets: {results[results['actual_upset'] == 0]['upset_prob'].mean():.3f}")
    #'''

def print_model_efficacy(results):
    print("\n=== Model Efficacy Analysis ===")
    print("Comparing model predictions to baseline seed differential probabilities\n")
    
    for seed_diff in sorted(results["seed_diff"].unique()):
        seed_data = results[results["seed_diff"] == seed_diff]
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
        
        print(f"Seed Diff {seed_diff} (baseline: {baseline_prob:.3f})")
        if higher_total > 0:
            print(f"  Model > Baseline: {higher_upsets}/{higher_total} upsets ({higher_upsets/higher_total:.3f})")
        else:
            print(f"  Model > Baseline: 0/0 upsets (N/A)")
        
        if lower_total > 0:
            print(f"  Model < Baseline: {lower_upsets}/{lower_total} upsets ({lower_upsets/lower_total:.3f})")
        else:
            print(f"  Model < Baseline: 0/0 upsets (N/A)")
        print()

print_model_efficacy(results)
#print_results_summary(results)