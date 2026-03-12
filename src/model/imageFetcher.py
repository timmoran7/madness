import requests
import json

url = "https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/teams?limit=400"
response = requests.get(url, verify=False)
data = response.json()

teams = {}
for team in data['sports'][0]['leagues'][0]['teams']:
    t = team['team']
    teams[t['displayName']] = {
        'id': t['id'],
        'logo': f"https://a.espncdn.com/i/teamlogos/ncaa/500/{t['id']}.png",
        'abbreviation': t['abbreviation']
    }

with open('team_logos.json', 'w') as f:
    json.dump(teams, f, indent=2)

print(f"Found {len(teams)} teams")