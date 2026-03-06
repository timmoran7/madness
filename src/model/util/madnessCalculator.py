import json
from pathlib import Path

# need to update if more teams are added otherwise will fail 
RANK_MIN = 1
RANK_MAX = 365
RANK_SPAN = RANK_MAX - RANK_MIN

def advantage_delta_to_score(dawg_rank, fav_rank):
	delta_norm = (fav_rank - dawg_rank) / RANK_SPAN
	return 5.0 + 5.0 * delta_norm

def ovr_rank_to_score(dawg_rank, fav_rank):
	if dawg_rank >= fav_rank:
		return 10.0

	rank_diff = (abs(dawg_rank - fav_rank)) / RANK_SPAN
	return 10.0 * 1.0 - rank_diff

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
	if(year == 2026):
		year = ''
	
	fileName = f"kpOvrStats{str(year)}.json"
	if stats_path is None:
		stats_path = Path(__file__).with_name(fileName)
		with open(stats_path, "r", encoding="utf-8") as f:
			return json.load(f)


def calculate_upset_correlations(team_a, team_b, stats=None):
	if stats is None:
		stats = load_kp_ovr_stats(None, 2025)

	if team_a not in stats or team_b not in stats:
		missing = [team for team in (team_a, team_b) if team not in stats]
		raise ValueError(f"Missing team(s) in stats: {', '.join(missing)}")

	a = stats[team_a]
	b = stats[team_b]

	if a["KenPom Ovr."] == b["KenPom Ovr."]:
		raise ValueError("Cannot determine underdog: teams have identical KenPom Ovr. rank")

	if a["KenPom Ovr."] > b["KenPom Ovr."]:
		dawg_name, dawg = team_a, a
		fav_name, fav = team_b, b
	else:
		dawg_name, dawg = team_b, b
		fav_name, fav = team_a, a

	rebound_off = advantage_delta_to_score(dawg["Off OR%"], fav["Off OR%"])
	rebound_def = advantage_delta_to_score(dawg["Def OR%"], fav["Def OR%"])
	rebounding = (0.7 * rebound_off) + (0.3 * rebound_def)

	to_off = advantage_delta_to_score(dawg["Off TO%"], fav["Off TO%"])
	to_def = advantage_delta_to_score(dawg["Def TO%"], fav["Def TO%"])
	turnovers = (0.5 * to_off) + (0.5 * to_def)

	dawg_volatility = three_point_pct_rank_to_score(dawg["Off 3PA"])
	fav_volatility = three_point_pct_rank_to_score(fav["Off 3PA"])
	three_pt_volume = (dawg_volatility + fav_volatility) / 2.0

	dawg_three_pct = three_point_pct_rank_to_score(dawg["Off 3P%"])
	dawg_pace = dawg_pace_rank_to_score(dawg["Tempo"], fav["Tempo"])

	ovr = ovr_rank_to_score(dawg["KenPom Ovr."], fav["KenPom Ovr."])
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
	madness_index = stats_mi * 0.67 + scores["ovr"] * 0.33
 
	# Hard for underdog to rank close/better to favorite in all these so attempt to account for the overall ranking gap
	madness_index *= 1.1
 
	return round(madness_index, 2)

if __name__ == "__main__":
	# Example usage
	try:
		result = calculate_upset_correlations("Michigan 2025", "UC San Diego 2025")
		madness_index = calculate_madness_index(result["scores"])
		print(json.dumps(result, indent=2))
		print(f"Madness Index: {madness_index}")
	except ValueError as e:
		print(f"Error: {e}")
