"""Themed Pokémon Center + Poké Mart backgrounds for every Kalos town that has one.

Uses the same Gen 5 room and recolor as Unova (make_unova_buildings.py): one picture per
town, saved under the two names the game asks for, [area]_center.png and [area]_mart.png.
Only the floor, walls, orange trim, Mart counter and plant change; every person and machine
stays as drawn.

    python dev/builders/make_kalos_buildings.py [town ...]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from make_sinnoh_buildings import BG  # noqa: E402
from make_unova_buildings import main as build  # noqa: E402

OUT = os.path.join(BG, "kalos")

THEMES = {
    # Riverside start town: river blue.
    "aquacorde": dict(wall="#3E7FB0", accent="#5AB0E0", floor="#F2E6C8", mart="#4AA8D8", plant="#4CAE60"),
    # Garden city with a bug gym: leaf green and rose.
    "santalune": dict(wall="#4E8A4E", accent="#D86A7A", floor="#F0E8C8", mart="#5AA8C8", plant="#3FA055"),
    # The city of light: Prism Tower gold on Parisian slate.
    "lumiose": dict(wall="#3A4258", accent="#D8A83A", floor="#EFE6D2", mart="#4A86C8", plant="#4A9A5A"),
    "lumiose_vert": dict(wall="#3E6A4A", accent="#5AAE6A", floor="#ECEFD8", mart="#4A9AB8", plant="#3FA055"),
    "lumiose_bleu": dict(wall="#2E4A7A", accent="#4A86D8", floor="#E6EAF2", mart="#3A7AC8", plant="#4A9A6A"),
    # Old castle town: weathered stone and moss.
    "camphrier": dict(wall="#6A6458", accent="#9A7A52", floor="#E4DCC8", mart="#5A86A0", plant="#5A8E4A"),
    # Seaside fossil town: sea and sand.
    "ambrette": dict(wall="#2E7AA0", accent="#3AA8A0", floor="#F4E6C4", mart="#3AA8C8", plant="#4CAE68"),
    # Cliffside rock city: canyon red and sandstone.
    "cyllage": dict(wall="#7A4A34", accent="#C8643A", floor="#EED6B4", mart="#4A8AB0", plant="#6A9A4A"),
    # Town of standing stones: grey stone and mystic violet.
    "geosenge": dict(wall="#4A4A5A", accent="#8A6AB0", floor="#DEDAD2", mart="#6A7AB0", plant="#5A8A5A"),
    # Mega Evolution tower town: sea breeze and Korrina orange.
    "shalour": dict(wall="#2E6A8A", accent="#F0882E", floor="#F2E8D2", mart="#3A9AC0", plant="#4AA868"),
    # Harbor town with the sun-and-moon garden: sunflower gold and green.
    "coumarine": dict(wall="#3A7A5A", accent="#E8B03A", floor="#F2E2C4", mart="#4AA0C0", plant="#4FAE5A"),
    # Fairy town in the old trees: pastel pink and wood.
    "laverre": dict(wall="#7A4A6A", accent="#F28AB8", floor="#FBEBEF", mart="#9A7AD0", plant="#5AAE6A"),
    # Windmill town in the cold: frost and windmill wood.
    "dendemille": dict(wall="#5A7A8A", accent="#C88A4A", floor="#EEF2F2", mart="#6AA0C8", plant="#3F8270"),
    # Sundial city: night blue and crystal violet.
    "anistar": dict(wall="#2E4A6A", accent="#8A6AD8", floor="#EEEAE0", mart="#4A86C8", plant="#4A9A6A"),
    # Waterfall rail town: rain and moss green.
    "couriway": dict(wall="#3E5A6A", accent="#5A9A7A", floor="#E4ECE4", mart="#4A8AB0", plant="#3FA060"),
    # Snowy city before the League: ice blue and white.
    "snowbelle": dict(wall="#5A86A8", accent="#8CC4E8", floor="#EEF5FA", mart="#6AAEE0", plant="#3F8270"),
    # Kalos League: royal crimson and gold.
    "league": dict(wall="#3A1E2A", accent="#C8A030", floor="#ECE2CC", mart="#8A3A4A", plant="#3E8E5A"),
    # Battle Maison resort town: violet and glam magenta.
    "kiloude": dict(wall="#4A3A6A", accent="#E06AA0", floor="#F2EAD4", mart="#7A6AC0", plant="#4A9A5A"),
}

OUTPUTS = {
    "aquacorde": ("aquacorde_town_center", "aquacorde_town_mart"),
    "santalune": ("santalune_city_center", "santalune_city_mart"),
    "lumiose": ("lumiose_city_center", "lumiose_city_mart"),
    "lumiose_vert": ("lumiose_vert_district_center", "lumiose_vert_district_mart"),
    "lumiose_bleu": ("lumiose_bleu_district_center", "lumiose_bleu_district_mart"),
    "camphrier": ("camphrier_town_center", "camphrier_town_mart"),
    "ambrette": ("ambrette_town_center", "ambrette_town_mart"),
    "cyllage": ("cyllage_city_center", "cyllage_city_mart"),
    "geosenge": ("geosenge_town_center", "geosenge_town_mart"),
    "shalour": ("shalour_city_center", "shalour_city_mart"),
    "coumarine": ("coumarine_city_center", "coumarine_city_mart"),
    "laverre": ("laverre_city_center", "laverre_city_mart"),
    "dendemille": ("dendemille_town_center", "dendemille_town_mart"),
    "anistar": ("anistar_city_center", "anistar_city_mart"),
    "couriway": ("couriway_town_center", "couriway_town_mart"),
    "snowbelle": ("snowbelle_city_center", "snowbelle_city_mart"),
    "league": ("kalos_pokemon_league_center", "kalos_pokemon_league_mart"),
    "kiloude": ("kiloude_city_center", "kiloude_city_mart"),
}

if __name__ == "__main__":
    build(sys.argv[1:] or list(OUTPUTS), THEMES, OUTPUTS, OUT)
