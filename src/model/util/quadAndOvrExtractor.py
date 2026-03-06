import json
import re
from html import unescape
from pathlib import Path
from typing import Optional

from bs4 import BeautifulSoup


QUAD_KEYS = ("q1", "q2", "q3", "q4")
KP_STAT_ID_MAP = {
	"Off Efficiency": "OE",
	"Def Efficiency": "DE",
	"Off TO%": "TOPct",
	"Def TO%": "DTOPct",
	"Off OR%": "ORPct",
	"Def OR%": "DORPct",
	"Off FT%": "FTPct",
	"Off 3PA": "3PARate",
	"A/FGM": "ARate",
	"Off 3P%": "3Pct",
	"Off Avg. Poss. Length": "APLO",
	"Def Avg. Poss. Length": "APLD",
	"Tempo": "Tempo",
}

ROW_STAT_LABEL_MAP = {
	"Average Height": "Average Height",
	"Minutes Continuity": "Minutes Continuity",
	"D-1 Experience": "D-1 Experience",
	"Bench Minutes": "Bench Minutes",
	"Overall": "SOS Overall",
	"Non-conference": "SOS Non-conference",
}


def clean_record(record_text: str) -> str:
	return record_text.replace("Record:", "").strip()


def extract_score(cell_text: str) -> str:
	match = re.search(r"\d+-\d+\*?", cell_text)
	return match.group(0) if match else cell_text.strip()


def extract_opponent_name(opponent_cell) -> str:
	opponent_link = opponent_cell.find("a")
	if opponent_link is None:
		return "Unknown"

	if opponent_link.get("title"):
		return unescape(opponent_link["title"]).strip()

	opponent_text = opponent_link.get_text(" ", strip=True)
	opponent_text = re.sub(r"^\d+\s+", "", opponent_text)
	return unescape(opponent_text).strip()


def format_game(score: str, location: str, opponent: str) -> str:
	location = location.strip()
	if location == "Away":
		return f"{score} @ {opponent}"
	if location == "Neutral":
		return f"{score} vs {opponent} (N)"
	return f"{score} vs {opponent}"


def extract_quad_data(team_soup: BeautifulSoup, quad_key: str) -> dict:
	quad_div = team_soup.select_one(f"div.{quad_key}.q")
	if quad_div is None:
		return {"record": "0-0", "games": []}

	record_node = quad_div.find("div", class_="quad-record")
	record_text = record_node.get_text(" ", strip=True) if record_node else "Record: 0-0"

	games = []
	for row in quad_div.select("table tr"):
		cells = row.find_all("td")
		if len(cells) < 6:
			continue

		score = extract_score(cells[1].get_text(" ", strip=True))
		location = cells[2].get_text(" ", strip=True)
		opponent = extract_opponent_name(cells[5])
		games.append(format_game(score, location, opponent))

	return {
		"record": clean_record(record_text),
		"games": games,
	}


def extractQuadStats(
	year,
) -> dict:
	source_dir = Path(__file__).parent / f"tempTeamQuads/{year}"
	target_file = Path(__file__).parent / f"quadStats{year}.json"

	if not source_dir.exists():
		raise FileNotFoundError(f"Input directory not found: {source_dir}")

	team_quad_stats = {}

	for txt_file in sorted(source_dir.glob("*.txt")):
		team_name = txt_file.stem.replace("_", " ")
		html = txt_file.read_text(encoding="utf-8", errors="ignore")
		soup = BeautifulSoup(html, "html.parser")

		team_quad_stats[team_name] = {
			quad_key: extract_quad_data(soup, quad_key)
			for quad_key in QUAD_KEYS
		}

	target_file.write_text(json.dumps(team_quad_stats, indent=2), encoding="utf-8")
	print(f"Saved quad stats for {len(team_quad_stats)} teams to {target_file}")

	return team_quad_stats


def extract_table_start_block(html: str) -> Optional[str]:
	table_start_match = re.search(r"function\s+tableStart\(\)\s*\{(.*?)\}\s*function\s+dechex", html, flags=re.DOTALL)
	if not table_start_match:
		return None
	return table_start_match.group(1)


def parse_rank_value_from_fragment(fragment: str) -> tuple[Optional[int], Optional[str]]:
	fragment_soup = BeautifulSoup(fragment, "html.parser")

	rank = None
	rank_node = fragment_soup.select_one("span.seed")
	if rank_node is not None:
		rank_match = re.search(r"\d+", rank_node.get_text(" ", strip=True))
		if rank_match:
			rank = int(rank_match.group(0))
		rank_node.decompose()

	value = None
	value_anchor = fragment_soup.find("a")
	if value_anchor is not None:
		value = value_anchor.get_text(" ", strip=True)
	else:
		text_value = fragment_soup.get_text(" ", strip=True)
		value = text_value or None

	return rank, value


def extract_rank_value_from_script(table_start_block: str, stat_id: str) -> tuple[Optional[int], Optional[str]]:
	pattern = rf'\$\(\s*"td#{re.escape(stat_id)}"\s*\)\.html\(\s*"(?P<html>(?:\\.|[^"\\])*)"\s*\);'
	match = re.search(pattern, table_start_block, flags=re.DOTALL)
	if not match:
		return None, None

	fragment = match.group("html")
	fragment = (
		fragment
		.replace(r'\"', '"')
		.replace(r"\'", "'")
		.replace(r"\\/", "/")
		.replace(r"\\n", " ")
		.replace(r"\\t", " ")
	)

	return parse_rank_value_from_fragment(fragment)


def extract_rank_value_from_cell(cell) -> tuple[Optional[int], Optional[str]]:
	cell_soup = BeautifulSoup(str(cell), "html.parser")

	rank = None
	rank_node = cell_soup.select_one("span.seed")
	if rank_node is not None:
		rank_match = re.search(r"\d+", rank_node.get_text(" ", strip=True))
		if rank_match:
			rank = int(rank_match.group(0))
		rank_node.decompose()

	value = None
	value_anchor = cell_soup.find("a")
	if value_anchor is not None:
		value = value_anchor.get_text(" ", strip=True)
	else:
		text_value = cell_soup.get_text(" ", strip=True)
		value = text_value or None

	return rank, value


def extract_row_based_stats(team_soup: BeautifulSoup) -> dict:
	report_table = team_soup.select_one("#report-table")
	row_stats = {output_key: [None, None] for output_key in ROW_STAT_LABEL_MAP.values()}
	if report_table is None:
		return row_stats

	for row in report_table.select("tr"):
		cells = row.find_all("td")
		if len(cells) < 2:
			continue

		label = cells[0].get_text(" ", strip=True).replace(":", "").strip()
		output_key = ROW_STAT_LABEL_MAP.get(label)
		if output_key is None:
			continue

		rank, value = extract_rank_value_from_cell(cells[1])
		row_stats[output_key] = [rank, value]

	return row_stats


def extract_overall_rank_value(team_soup: BeautifulSoup) -> tuple[Optional[int], Optional[str]]:
	title_node = team_soup.select_one("#title-container h5")
	if title_node is None:
		return None, None

	rank_nodes = title_node.select("span.rank")
	if not rank_nodes:
		return None, None

	rank = None
	match = re.search(r"\d+", rank_nodes[0].get_text(" ", strip=True))
	if match:
		rank = int(match.group(0))

	value = None
	if len(rank_nodes) > 1:
		record_text = rank_nodes[1].get_text(" ", strip=True)
		value = record_text.strip("()") if record_text else None

	return rank, value


def extractKpOvrStats(
	year,
) -> dict:
	source_dir = Path(__file__).parent / f"tempTeamPhps/{year}"
	target_file = Path(__file__).parent / f"kpOvrStats{year}.json"

	if not source_dir.exists():
		raise FileNotFoundError(f"Input directory not found: {source_dir}")

	team_stat_ranks = {}
	txt_files = sorted(source_dir.glob("*.txt"))

	for txt_file in txt_files:
		html = txt_file.read_text(encoding="utf-8", errors="ignore")
		soup = BeautifulSoup(html, "html.parser")
		team_name = txt_file.stem.replace("_", " ")
		table_start_block = extract_table_start_block(html)

		overall_rank, overall_value = extract_overall_rank_value(soup)
		stats = {"KenPom Ovr.": [overall_rank, overall_value]}
		for output_key, stat_id in KP_STAT_ID_MAP.items():
			rank, value = (None, None)
			if table_start_block is not None:
				rank, value = extract_rank_value_from_script(table_start_block, stat_id)
			stats[output_key] = [rank, value]

		stats.update(extract_row_based_stats(soup))

		team_stat_ranks[team_name] = stats

	target_file.write_text(json.dumps(team_stat_ranks, indent=2), encoding="utf-8")
	print(f"Saved KenPom ranks for {len(team_stat_ranks)} teams to {target_file}")

	return team_stat_ranks

if __name__ == "__main__":
    #extractKpOvrStats(2026)
	extractQuadStats(2025)
