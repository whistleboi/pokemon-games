import requests
import json
import os

print("Fetching real Pokémon names from PokeAPI...")

response = requests.get("https://pokeapi.co/api/v2/pokemon?limit=1010")
data = response.json()

names = {}
for i, pokemon in enumerate(data["results"], 1):
    names[str(i)] = pokemon["name"]   # lowercase exactly as PokeAPI uses

# Make sure the assets folder exists
os.makedirs("assets", exist_ok=True)

with open("assets/pokemon_names.json", "w") as f:
    json.dump(names, f, indent=2)

print("✅ Done! pokemon_names.json is ready in the assets folder.")
print("   Your game will now show real names like BULBASAUR, PIKACHU, etc.")