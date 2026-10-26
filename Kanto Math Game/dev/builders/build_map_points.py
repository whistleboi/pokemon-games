"""Town positions on assets/world_map 2.png (Jordan's world map in the Town Map style) for the region
maps and Fly (src/states/region_map.py), written to assets/map_points.json:

  views:  map name -> [x0, y0, x1, y1], the part of the world map each region's map shows
  points: area key -> [x, y], where the town sits (world-map pixels)

Towns are matched to the map's own markers (red / blue / green squares, found here by colour);
the few drawn as L shapes or not marked get a hand-placed spot. Matching was done by eye against
each game's real Town Map. Run from the game folder:  python dev/builders/build_map_points.py
"""
import json
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame  # noqa: E402

MAP = "assets/world_map 2.png"


def find_markers(img):
    """Solid red / blue / green squares (the map's town and landmark markers), in scan order."""
    w, h = img.get_size()
    raw = pygame.image.tobytes(img, "RGB")

    def kind(x, y):
        i = (y * w + x) * 3
        r, g, b = raw[i], raw[i + 1], raw[i + 2]
        if r > 200 and g < 120 and b < 120:
            return "red"
        if abs(r - 111) < 14 and abs(g - 135) < 14 and b > 225:
            return "blue"
        if abs(r - 143) < 6 and abs(g - 208) < 6 and b < 50:
            return "green"
        return None
    grid = [[kind(x, y) for x in range(w)] for y in range(h)]
    seen = [[False] * w for _ in range(h)]
    out = []
    for y in range(h):
        for x in range(w):
            k = grid[y][x]
            if not k or seen[y][x]:
                continue
            stack, pts = [(x, y)], []
            seen[y][x] = True
            while stack:
                a, b = stack.pop()
                pts.append((a, b))
                for c, d in ((a + 1, b), (a - 1, b), (a, b + 1), (a, b - 1)):
                    if 0 <= c < w and 0 <= d < h and not seen[d][c] and grid[d][c] == k:
                        seen[d][c] = True
                        stack.append((c, d))
            xs, ys = [p[0] for p in pts], [p[1] for p in pts]
            bw, bh = max(xs) - min(xs) + 1, max(ys) - min(ys) + 1
            if len(pts) >= 12 and len(pts) >= 0.6 * bw * bh and bw <= 30 and bh <= 30:
                out.append(((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2))
    return out


VIEWS = {
    "KANTO": [975, 850, 1210, 1015], "SEVII": [1070, 1035, 1205, 1200], "JOHTO": [835, 875, 1045, 1030],
    "HOENN": [585, 880, 815, 1010], "ORRE": [580, 740, 770, 885], "SINNOH": [1140, 390, 1385, 600],
    "UNOVA": [285, 650, 535, 845], "DECOLORE": [315, 935, 475, 1085], "KALOS": [240, 400, 470, 560],
    "ALOLA": [545, 1085, 815, 1255], "GALAR": [60, 150, 245, 625], "PALDEA": [105, 665, 290, 835],
    "ORANGE": [835, 1015, 1005, 1265],
}
# Which view each region's towns belong to (sub-regions get their own map).
VIEW_OF_REGION = {"KANTO": "KANTO", "JOHTO": "JOHTO", "HOENN": "HOENN", "SINNOH": "SINNOH", "UNOVA": "UNOVA",
                  "KALOS": "KALOS", "ALOLA": "ALOLA", "GALAR": "GALAR", "PALDEA": "PALDEA", "ORANGE": "ORANGE",
                  "ORRE": "ORRE"}
SUB_VIEWS = {"SEVII": ["ONE_ISLAND", "TWO_ISLAND", "THREE_ISLAND", "FOUR_ISLAND", "FIVE_ISLAND", "SIX_ISLAND",
                       "SEVEN_ISLAND"],
             "DECOLORE": ["HONEY_ISLAND", "SCALCHOP_ISLAND", "GRAND_SPECTRALA_ISLAND", "TOROM_ISLAND",
                          "PALADIN_ISLAND"]}

# Area -> marker number (find_markers order) ...
MARKER = {
    # Kanto (FireRed / LeafGreen)
    "PALLET_TOWN": 250, "VIRIDIAN_CITY": 235, "PEWTER_CITY": 207, "CERULEAN_CITY": 206, "VERMILLION_CITY": 238,
    "LAVENDER_TOWN": 222, "CELADON_CITY": 223, "SAFFRON_CITY": 224, "FUCHSIA_CITY": 253, "CINNABAR_ISLAND": 262,
    "ROCK_TUNNEL_CITY": 208, "INDIGO_PLATEAU": 204,
    # Sevii Islands
    "ONE_ISLAND": 272, "TWO_ISLAND": 271, "THREE_ISLAND": 273, "FOUR_ISLAND": 277, "FIVE_ISLAND": 278,
    "SIX_ISLAND": 286, "SEVEN_ISLAND": 288,
    # Johto (HeartGold / SoulSilver)
    "NEW_BARK_TOWN": 255, "CHERRYGROVE_CITY": 254, "VIOLET_CITY": 231, "AZALEA_TOWN": 266, "GOLDENROD_CITY": 245,
    "ECRUTEAK_CITY": 213, "OLIVINE_CITY": 227, "CIANWOOD_CITY": 247, "MAHOGANY_TOWN": 219, "BLACKTHORN_CITY": 214,
    # Hoenn (Ruby / Sapphire / Emerald)
    "LITTLEROOT_TOWN": 251, "OLDALE_TOWN": 244, "PETALBURG_CITY": 243, "DEWFORD_TOWN": 259, "SLATEPORT_CITY": 249,
    "MAUVILLE_CITY": 234, "VERDANTURF_TOWN": 233, "FALLARBOR_TOWN": 210, "LAVARIDGE_TOWN": 225,
    "FORTREE_CITY": 211, "LILYCOVE_CITY": 226, "MOSSDEEP_CITY": 232, "SOOTOPOLIS_CITY": 237,
    "PACIFIDLOG_TOWN": 248, "EVER_GRANDE_CITY": 241,
    # Orre (Colosseum / XD)
    "PHENAC_CITY": 200, "PYRITE_TOWN": 198, "GATEON_PORT": 197, "AGATE_VILLAGE": 178, "REALGAM_TOWER": 163,
    # Sinnoh (Diamond / Pearl / Platinum)
    "TWINLEAF_TOWN": 122, "SANDGEM_TOWN": 121, "JUBILIFE_CITY": 118, "CANALAVE_CITY": 114, "FLOAROMA_TOWN": 105,
    "HEARTHOME_CITY": 111, "SOLACEON_TOWN": 109, "CELESTIC_TOWN": 90, "VEILSTONE_CITY": 96, "PASTORIA_CITY": 120,
    "SUNYSHORE_CITY": 117, "SINNOH_POKEMON_LEAGUE": 93, "SNOWPOINT_CITY": 61,
    "FIGHT_AREA": 80, "SURVIVAL_AREA": 70, "RESORT_AREA": 85,
    # Unova (Black / White, Black 2 / White 2)
    "NUVEMA_TOWN": 196, "ACCUMULA_TOWN": 190, "NACRENE_CITY": 181, "CASTELIA_CITY": 182, "NIMBASA_CITY": 167,
    "DRIFTVEIL_CITY": 162, "OPELUCID_CITY": 144, "UNOVA_POKEMON_LEAGUE": 140, "LACUNOSA_TOWN": 143,
    "UNDELLA_TOWN": 150, "BLACK_CITY": 149, "HUMILAU_CITY": 145, "ASPERTIA_CITY": 183, "FLOCCESY_TOWN": 173,
    "VIRBANK_CITY": 174, "LENTIMAS_TOWN": 142,
    # Decolore Islands
    "HONEY_ISLAND": 236, "SCALCHOP_ISLAND": 242, "GRAND_SPECTRALA_ISLAND": 268, "TOROM_ISLAND": 275,
    "PALADIN_ISLAND": 270,
    # Kalos (X / Y)
    "LUMIOSE_CITY": 79, "SANTALUNE_CITY": 94, "AQUACORDE_TOWN": 108, "VANIVILLE_TOWN": 113, "CAMPHRIER_TOWN": 102,
    "AMBRETTE_TOWN": 101, "CYLLAGE_CITY": 92, "GEOSENGE_TOWN": 77, "SHALOUR_CITY": 67, "COUMARINE_CITY": 59,
    "LAVERRE_CITY": 68, "DENDEMILLE_TOWN": 78, "ANISTAR_CITY": 86, "COURIWAY_TOWN": 95,
    "KALOS_POKEMON_LEAGUE": 84, "KILOUDE_CITY": 112,
    # Alola (Sun / Moon)
    "IKI_TOWN": 276, "HAUOLI_CITY": 279, "HEAHEA_CITY": 283, "PANIOLA_TOWN": 280, "KONIKONI_CITY": 285,
    "HANO_GRAND_RESORT": 281, "MALIE_CITY": 290, "HOKULANI_OBSERVATORY": 291, "TAPU_VILLAGE": 293,
    "SEAFOLK_VILLAGE": 287,
    # Galar (Sword / Shield)
    "WYNDON": 8, "HAMMERLOCKE": 54, "MOTOSTOKE": 83, "STOW_ON_SIDE": 44, "BALLONLEA": 27, "CIRCHESTER": 23,
    "SPIKEMUTH": 35, "HULBURY": 72, "WEDGEHURST": 91, "POSTWICK": 119,
    # Paldea (Scarlet / Violet)
    "MESAGOZA": 172, "CABO_POCO": 188, "CORTONDO": 187, "ARTAZON": 175, "LEVINCIA": 158, "CASCARRAFA": 160,
    "PORTO_MARINADA": 157, "MEDALI": 151, "MONTENEVERA": 141, "GLASEADO": 147, "ALFORNADA": 176,
    # Orange Islands (the anime)
    "VALENCIA_ISLAND": 269, "NAVEL_ISLAND": 282, "PUMMELO_ISLAND": 292, "SHAMOUTI_ISLAND": 284,
}
# ... or a hand-placed spot (L-shaped towns, unmarked places), world-map pixels.
SPOT = {
    "MT_MOON_CITY": [1098, 901], "BILLS_HOUSE": [1175, 875], "UNDERGROUND_PATH": [1153, 943],
    "POKEMON_LEAGUE_GATE": [1022, 944], "MT_SILVER_CITY": [1004, 945], "SILVER_LEAGUE_PLATEAU": [1004, 932],
    "MR_POKEMONS_HOUSE": [958, 960], "RUINS_OF_ALPH": [928, 956],
    "RUSTBORO_CITY": [620, 938],
    "ETERNA_CITY": [1235, 480], "OREBURGH_CITY": [1228, 533],
    "STRIATON_CITY": [503, 798], "MISTRALTON_CITY": [350, 743], "ICIRRUS_CITY": [380, 718],
    "SNOWBELLE_CITY": [435, 430], "ALOLA_POKEMON_LEAGUE": [771, 1220],
    "TURFFIELD": [135, 450], "MEETUP_SPOT": [175, 415],
    "PALDEA_RUINOUS_SHRINES": [181, 759], "TERARIUM_CENTRAL_PLAZA": [276, 822], "BLUEBERRY_ACADEMY": [282, 818],
    "KITAKAMI_HALL": [275, 681], "MOSSUI_TOWN": [281, 685],
    "MIKAN_ISLAND": [925, 1104], "PINKAN_ISLAND": [878, 1099], "TROVITA_ISLAND": [848, 1168],
    "KUMQUAT_ISLAND": [866, 1218], "SUNBURST_ISLAND": [993, 1104],
}
# Next to another town's marker (same place, a step away).
NEAR = {"SILPH_CITY": "SAFFRON_CITY", "OLIVINE_LIGHTHOUSE": "OLIVINE_CITY",
        "ECRUTEAK_DANCE_THEATER": "ECRUTEAK_CITY", "JUBILIFE_VILLAGE": "JUBILIFE_CITY",
        "SINJOH_CABIN": "CELESTIC_TOWN", "NARANJA_ACADEMY": "MESAGOZA", "BIG_WAVE_BEACH": "HANO_GRAND_RESORT"}

pygame.display.init()
pygame.display.set_mode((1, 1))
markers = find_markers(pygame.image.load(MAP))
points = {k: [round(markers[i][0], 1), round(markers[i][1], 1)] for k, i in MARKER.items()}
points.update(SPOT)
for k, other in NEAR.items():
    x, y = points[other]
    points[k] = [x + 6, y + 6]
json.dump({"map": os.path.basename(MAP), "views": VIEWS, "sub_views": SUB_VIEWS, "points": points},
          open("assets/map_points.json", "w", encoding="utf-8"), indent=1)
print(len(markers), "markers;", len(points), "towns placed")
