import json

# Read the existing matchups file
with open('/home/tmoran/personal/itsmarch/src/model/matchups/2025.json', 'r') as f:
    matchups = json.load(f)

# Read the postseason entries
with open('/home/tmoran/personal/itsmarch/src/model/util/postseason_entries.json', 'r') as f:
    postseason = json.load(f)

# Combine them
all_matchups = matchups + postseason

# Write back to the file
with open('/home/tmoran/personal/itsmarch/src/model/matchups/2025.json', 'w') as f:
    json.dump(all_matchups, f, indent=2)

print(f"Successfully appended {len(postseason)} postseason games to matchups/2025.json")
print(f"Total matchups: {len(all_matchups)}")
