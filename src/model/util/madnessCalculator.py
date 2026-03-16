import json
from pathlib import Path
from itertools import combinations

# need to update if more teams are added otherwise will fail 
RANK_MIN = 1
RANK_MAX = 365
RANK_SPAN = RANK_MAX - RANK_MIN
FACTOR_COLUMNS = ["Rebounding", "Turnovers", "3Pt Volume", "Dawg 3P%", "Dawg Pace"]
FACTOR_KEY_ORDER = ["rebounding", "turnovers", "3pt_volume", "dawg_3p_pct", "dawg_pace"]


def normalize_team_name(name):
	return name.replace(".", "").replace("'", "")


def extract_rank(stat_value):
	if isinstance(stat_value, list):
		if not stat_value:
			raise ValueError("Encountered empty stat list")
		stat_value = stat_value[0]

	return float(stat_value)


def resolve_team_stats(team_name, stats):
	if team_name in stats:
		return team_name, stats[team_name]

	normalized_name = normalize_team_name(team_name)
	for stats_team_name, team_stats in stats.items():
		if normalize_team_name(stats_team_name) == normalized_name:
			return stats_team_name, team_stats

	raise ValueError(f"Missing team in stats: {team_name}")

def advantage_delta_to_score(dawg_rank, fav_rank):
	delta_norm = (fav_rank - dawg_rank) / RANK_SPAN
	return 5.0 + 5.0 * delta_norm

def ovr_rank_to_score(dawg_rank, fav_rank):
	if fav_rank > dawg_rank:
		return 10.0

	rank_diff = (abs(dawg_rank - fav_rank)) / RANK_SPAN
	return 10.0 * (1.0 - rank_diff)

def three_point_pct_rank_to_score(rank):
	return ((RANK_MAX + 1 - rank) / RANK_MAX) * 10.0

# slower dawg tempo is better, unsure of affect of fav tempo in this situation so dont include 
# fav tempo in calc but prevent super high factor (> 8.5)
# fast dawg tempo is generally worse, but better if fav is slow -- bringing out of comfort zone.
def dawg_pace_rank_to_score(dawg_rank, fav_rank):
    raw_factor = 1.5 + ((dawg_rank / RANK_MAX) * 7.0)
    if dawg_rank < (RANK_SPAN / 2) and fav_rank - dawg_rank > (RANK_SPAN / 4):
        delta_factor = 1.5 + (((fav_rank - dawg_rank) / RANK_MAX) * 7.0)
        return (raw_factor + delta_factor) / 2.0
    
    return raw_factor

def load_kp_ovr_stats(stats_path=None, year=2026):
	fileName = f"kpOvrStats{str(year)}.json"
	if stats_path is None:
		stats_path = Path(__file__).resolve().with_name(fileName)

	with open(stats_path, "r", encoding="utf-8") as f:
		return json.load(f)


def load_matchups_by_region(matchups_path=None, year=2026):
	if matchups_path is None:
		matchups_path = Path(__file__).with_name(f"matchups{year}.json")
	else:
		matchups_path = Path(matchups_path)

	with open(matchups_path, "r", encoding="utf-8") as f:
		matchup_data = json.load(f)

	if not isinstance(matchup_data, dict):
		raise ValueError("Matchups file must be a JSON object.")

	if isinstance(matchup_data.get("regions"), dict):
		return matchup_data["regions"], matchup_data.get("locations")

	return matchup_data, None


def calculate_upset_correlations(team_a, team_b, stats=None):
	if stats is None:
		stats = load_kp_ovr_stats(None, 2026)

	missing = []
	try:
		_, a = resolve_team_stats(team_a, stats)
	except ValueError:
		missing.append(team_a)

	try:
		_, b = resolve_team_stats(team_b, stats)
	except ValueError:
		missing.append(team_b)

	if missing:
		raise ValueError(f"Missing team(s) in stats: {', '.join(missing)}")

	a_ovr = extract_rank(a["KenPom Ovr."])
	b_ovr = extract_rank(b["KenPom Ovr."])

	if a_ovr == b_ovr:
		raise ValueError("Cannot determine underdog: teams have identical KenPom Ovr. rank")

	if a_ovr > b_ovr:
		dawg_name, dawg = team_a, a
		fav_name, fav = team_b, b
	else:
		dawg_name, dawg = team_b, b
		fav_name, fav = team_a, a

	rebound_off = advantage_delta_to_score(extract_rank(dawg["Off OR%"]), extract_rank(fav["Off OR%"]))
	rebound_def = advantage_delta_to_score(extract_rank(dawg["Def OR%"]), extract_rank(fav["Def OR%"]))
	rebounding = (0.7 * rebound_off) + (0.3 * rebound_def)

	to_off = advantage_delta_to_score(extract_rank(dawg["Off TO%"]), extract_rank(fav["Off TO%"]))
	to_def = advantage_delta_to_score(extract_rank(dawg["Def TO%"]), extract_rank(fav["Def TO%"]))
	turnovers = (0.5 * to_off) + (0.5 * to_def)

	dawg_volatility = three_point_pct_rank_to_score(extract_rank(dawg["Off 3PA"]))
	fav_volatility = three_point_pct_rank_to_score(extract_rank(fav["Off 3PA"]))
	three_pt_volume = (dawg_volatility + fav_volatility) / 2.0

	dawg_three_pct = three_point_pct_rank_to_score(extract_rank(dawg["Off 3P%"]))
	dawg_pace = dawg_pace_rank_to_score(extract_rank(dawg["Tempo"]), extract_rank(fav["Tempo"]))

	ovr = ovr_rank_to_score(extract_rank(dawg["KenPom Ovr."]), extract_rank(fav["KenPom Ovr."]))
	scores = {
		"rebounding": round(rebounding, 2),
		"turnovers": round(turnovers, 2),
		"3pt_volume": round(three_pt_volume, 2),
		"dawg_3p_pct": round(dawg_three_pct, 2),
		"dawg_pace": round(dawg_pace, 2),
		"ovr": round(ovr, 2),
	}

	return {
		"favorite": fav_name,
		"underdog": dawg_name,
		"scores": scores,
	}

def calculate_madness_index(scores):
	# Weights for each factor (these can be adjusted based on importance)
	weights = {
		"rebounding": 0.15,
		"turnovers": 0.25,
		"3pt_volume": 0.3,
		"dawg_3p_pct": 0.2,
		"dawg_pace": 0.1,
	}

	stats_mi = sum(scores[factor] * weight for factor, weight in weights.items())
	madness_index = stats_mi * 0.8 + scores["ovr"] * 0.2
 
	# Hard for underdog to rank close/better to favorite in all these so attempt to account for the overall ranking gap
 
	return round(madness_index, 2)

def add_madness_data_to_upset_file(
	year=2026,
	fullMode=False,
	matchups_path=None,
	upset_data_path=None,
	stats_path=None,
):
	regions, file_locations = load_matchups_by_region(matchups_path=matchups_path, year=year)
	stats = load_kp_ovr_stats(stats_path=stats_path, year=year)

	if upset_data_path is None:
		upset_data_path = Path(__file__).resolve().with_name("upsetData.json")
	else:
		upset_data_path = Path(upset_data_path)

	if upset_data_path.exists():
		with open(upset_data_path, "r", encoding="utf-8") as f:
			upset_data = json.load(f)
	else:
		upset_data = {}

	matchup_data = {}
	current_matchups = upset_data.get("matchups", {})
	locations = file_locations if isinstance(file_locations, dict) else upset_data.get("locations")
	matchups_to_process = []
	unique_teams = set()
	seen_matchups = set()

	for region_matchups in regions.values():
		for matchup in region_matchups:
			teams = matchup.split("_", 1)
			if len(teams) != 2:
				raise ValueError(f"Invalid matchup format: {matchup}")

			team_a, team_b = teams
			unique_teams.add(team_a)
			unique_teams.add(team_b)

			if matchup not in seen_matchups:
				matchups_to_process.append((matchup, team_a, team_b))
				seen_matchups.add(matchup)

	if fullMode:
		sorted_teams = sorted(unique_teams)
		for team_a, team_b in combinations(sorted_teams, 2):
			direct_key = f"{team_a}_{team_b}"
			reverse_key = f"{team_b}_{team_a}"

			if direct_key in current_matchups:
				matchup_key = direct_key
			elif reverse_key in current_matchups:
				matchup_key = reverse_key
			else:
				matchup_key = direct_key

			if matchup_key in seen_matchups:
				continue

			matchups_to_process.append((matchup_key, team_a, team_b))
			seen_matchups.add(matchup_key)

	for matchup, team_a, team_b in matchups_to_process:
			result = calculate_upset_correlations(team_a, team_b, stats=stats)
			scores = result["scores"]

			entry = current_matchups.get(matchup, {})
			entry["index"] = calculate_madness_index(scores)
			entry["factors"] = [f"{scores[key]:.2f}" for key in FACTOR_KEY_ORDER]
			if "upset" not in entry:
				entry["upset"] = 0.0

			matchup_data[matchup] = entry

	upset_data["columns"] = FACTOR_COLUMNS
	upset_data["regions"] = regions
	upset_data["matchups"] = matchup_data
	if isinstance(locations, dict):
		upset_data["locations"] = locations

	with open(upset_data_path, "w", encoding="utf-8") as f:
		json.dump(upset_data, f, indent=2)

	return upset_data

if __name__ == "__main__":
	# Example usage
	try:
		add_madness_data_to_upset_file(2026,True,upset_data_path="../upsetData.json")
		# result = calculate_upset_correlations("Michigan", "UC San Diego")
		# madness_index = calculate_madness_index(result["scores"])
		# print(json.dumps(result, indent=2))
		# print(f"Madness Index: {madness_index}")
	except ValueError as e:
		print(f"Error: {e}")
