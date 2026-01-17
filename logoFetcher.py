import requests
import os

# URL of the logo
url = "https://content.sportslogos.net/logos/30/596/full/akron_zips_logo_primary_2022_sportslogosnet-8974.png"

# Create the logos directory if it doesn't exist
os.makedirs("public/logos", exist_ok=True)

# Fetch the image (SSL verification disabled)
response = requests.get(url, verify=False)
response.raise_for_status()

# Save the image
with open("public/logos/akronTest.png", "wb") as f:
    f.write(response.content)

print("Logo saved successfully to public/logos/akronTest.png")
