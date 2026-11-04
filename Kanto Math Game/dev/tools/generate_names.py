import requests
import json
import os

print("Fetching real Pokémon names from PokeAPI...")

response = requests.get("https://pokeapi.co/api/v2/pokemon?limit=1025")
data = response.json()

names = {}
for i, pokemon in enumerate(data["results"], 1):
    names[str(i)] = pokemon["name"]   # lowercase exactly as PokeAPI uses

# The game's assets folder, two levels up from dev/tools.
script_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # the game folder (this is dev/tools)
assets_dir = os.path.join(script_dir, 'assets')

# Make sure the assets folder exists
os.makedirs(assets_dir, exist_ok=True)

with open(os.path.join(assets_dir, "pokemon_names.json"), "w") as f:
    json.dump(names, f, indent=2)

print("✅ Done! pokemon_names.json is ready in the assets folder.")
print("   Your game will now show real names like BULBASAUR, PIKACHU, etc.")