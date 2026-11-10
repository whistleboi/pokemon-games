"""Region maps for Fly, the Town Map and the Pokedex's area view (Jordan, 10-30), from Pokemon
Journeys V18's Essentials town maps (Graphics/Pictures/mapRegionN.png, 480x320):
0 Kanto, 1 Johto, 2 Hoenn, 3 Sinnoh, 4 Unova, 5 Kalos, 6 Alola, 7 Galar, 8 Sevii, 9 Orange, 10 Orre,
11 Decolore (Paldea has none: it keeps the world map).

Each map is copied to assets/region_maps/<view>.png and every area of that view gets a point (map
pixels) in assets/map_points.json under "region_maps":
- Kanto and Johto: Journeys' own points (PBS/townmap.txt), matched to our areas by name;
- the rest: placed by hand on each map's town squares (ASSIGN below, map pixels).
Galar's map: Galar (north) and the Crown Tundra (south) on the long landmass, the Isle of Armor on the
right. Paldea has no map: it keeps the world map.
Writes a preview of each map with its points to dev/builders/out/region_maps/ for checking by eye.

    python dev/builders/build_region_maps.py ["<Pokemon Journeys V18 folder>"]
"""
import glob
import json
import os
import re
import shutil
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame  # noqa: E402

JOURNEYS = sys.argv[1] if len(sys.argv) > 1 else os.path.join("..", "..", "Pokemon Journeys V18")
PICS = os.path.join(JOURNEYS, "Graphics", "Pictures")
OUT = os.path.join("assets", "region_maps")
PREVIEW = os.path.join("dev", "builders", "out", "region_maps")
MAPS = {"KANTO": 0, "JOHTO": 1, "HOENN": 2, "SINNOH": 3, "UNOVA": 4, "KALOS": 5, "ALOLA": 6, "GALAR": 7,
        "SEVII": 8, "ORANGE": 9, "ORRE": 10, "DECOLORE": 11}
# placed by hand: [x, y] in map pixels (480x320; Sinnoh, Alola and Orre are 420 wide), each on its town square
ASSIGN = {
    "KANTO": {"PALLET_TOWN": [102, 238], "VIRIDIAN_CITY": [102, 174], "PEWTER_CITY": [110, 57],
              "CERULEAN_CITY": [322, 50], "VERMILLION_CITY": [322, 192], "LAVENDER_TOWN": [378, 128],
              "CELADON_CITY": [259, 128], "SAFFRON_CITY": [322, 126], "FUCHSIA_CITY": [284, 258],
              "CINNABAR_ISLAND": [102, 296], "INDIGO_PLATEAU": [29, 42], "ROCK_TUNNEL_CITY": [377, 67],
              "MT_MOON_CITY": [194, 66], "BILLS_HOUSE": [460, 12], "UNDERGROUND_PATH": [312, 165],
              "POKEMON_LEAGUE_GATE": [30, 165], "SILPH_CITY": [330, 120]},
    "JOHTO": {"ECRUTEAK_DANCE_THEATER": [263, 75], "POKEATHLON_DOME": [182, 121], "OLIVINE_LIGHTHOUSE": [140, 118],
              "MR_POKEMONS_HOUSE": [323, 131], "MT_SILVER_CITY": [470, 35], "SILVER_LEAGUE_PLATEAU": [470, 48]},
    "HOENN": {"LITTLEROOT_TOWN": [107, 228], "OLDALE_TOWN": [107, 195], "PETALBURG_CITY": [72, 194],
              "RUSTBORO_CITY": [50, 125], "DEWFORD_TOWN": [79, 272], "SLATEPORT_CITY": [166, 222],
              "MAUVILLE_CITY": [163, 140], "VERDANTURF_TOWN": [107, 139], "FALLARBOR_TOWN": [92, 54],
              "LAVARIDGE_TOWN": [130, 103], "FORTREE_CITY": [214, 54], "LILYCOVE_CITY": [315, 110],
              "MOSSDEEP_CITY": [401, 129], "SOOTOPOLIS_CITY": [355, 164], "PACIFIDLOG_TOWN": [294, 214],
              "EVER_GRANDE_CITY": [439, 181]},
    "SINNOH": {"TWINLEAF_TOWN": [103, 257], "SANDGEM_TOWN": [122, 244], "JUBILIFE_CITY": [115, 215],
               "JUBILIFE_VILLAGE": [115, 215], "CANALAVE_CITY": [77, 203], "FLOAROMA_TOWN": [122, 175],
               "OREBURGH_CITY": [158, 213], "ETERNA_CITY": [171, 138], "HEARTHOME_CITY": [223, 190],
               "SOLACEON_TOWN": [256, 173], "CELESTIC_TOWN": [220, 134], "VEILSTONE_CITY": [290, 153],
               "PASTORIA_CITY": [258, 235], "SUNYSHORE_CITY": [357, 213], "SINNOH_POKEMON_LEAGUE": [351, 145],
               "SNOWPOINT_CITY": [184, 48], "FIGHT_AREA": [278, 104], "SURVIVAL_AREA": [285, 68],
               "RESORT_AREA": [337, 116], "SINJOH_CABIN": [221, 150]},
    "UNOVA": {"NUVEMA_TOWN": [410, 285], "ACCUMULA_TOWN": [410, 257], "STRIATON_CITY": [403, 224],
              "NACRENE_CITY": [361, 221], "CASTELIA_CITY": [252, 238], "NIMBASA_CITY": [334, 172],
              "DRIFTVEIL_CITY": [159, 164], "MISTRALTON_CITY": [95, 132], "ICIRRUS_CITY": [157, 87],
              "OPELUCID_CITY": [236, 73], "UNOVA_POKEMON_LEAGUE": [306, 26], "LACUNOSA_TOWN": [408, 59],
              "UNDELLA_TOWN": [401, 122], "BLACK_CITY": [344, 122], "HUMILAU_CITY": [448, 122],
              "ASPERTIA_CITY": [57, 235], "FLOCCESY_TOWN": [76, 202], "VIRBANK_CITY": [148, 203],
              "LENTIMAS_TOWN": [61, 49]},
    "KALOS": {"LUMIOSE_CITY": [245, 139], "SANTALUNE_CITY": [292, 211], "AQUACORDE_TOWN": [293, 254],
              "VANIVILLE_TOWN": [293, 295], "CAMPHRIER_TOWN": [208, 232], "AMBRETTE_TOWN": [98, 232],
              "CYLLAGE_CITY": [23, 191], "GEOSENGE_TOWN": [49, 129], "SHALOUR_CITY": [152, 66],
              "COUMARINE_CITY": [255, 25], "LAVERRE_CITY": [349, 67], "DENDEMILLE_TOWN": [449, 129],
              "ANISTAR_CITY": [461, 165], "COURIWAY_TOWN": [404, 212], "SNOWBELLE_CITY": [342, 295],
              "KALOS_POKEMON_LEAGUE": [359, 160], "KILOUDE_CITY": [98, 288]},
    "ALOLA": {"IKI_TOWN": [170, 55], "HAUOLI_CITY": [163, 80], "HEAHEA_CITY": [253, 128],
              "PANIOLA_TOWN": [262, 94], "HANO_GRAND_RESORT": [295, 109], "KONIKONI_CITY": [262, 153],
              "BIG_WAVE_BEACH": [275, 141], "MALIE_CITY": [316, 186], "HOKULANI_OBSERVATORY": [348, 207],
              "TAPU_VILLAGE": [343, 272], "ALOLA_POKEMON_LEAGUE": [363, 245], "SEAFOLK_VILLAGE": [63, 163]},
    "GALAR": {"WYNDON": [203, 40], "CIRCHESTER": [233, 71], "SPIKEMUTH": [250, 105], "BALLONLEA": [178, 66],
              "STOW_ON_SIDE": [178, 88], "HAMMERLOCKE": [204, 97], "TURFFIELD": [179, 126],
              "HULBURY": [246, 126], "MOTOSTOKE": [208, 145], "MEETUP_SPOT": [210, 168],
              "WEDGEHURST": [229, 194], "POSTWICK": [213, 218]},
    "SEVII": {"ONE_ISLAND": [108, 58], "TWO_ISLAND": [215, 45], "THREE_ISLAND": [318, 61],
              "FOUR_ISLAND": [151, 135], "FIVE_ISLAND": [343, 154], "SIX_ISLAND": [307, 236],
              "SEVEN_ISLAND": [129, 244]},
    "ORANGE": {"VALENCIA_ISLAND": [217, 64], "MIKAN_ISLAND": [225, 88], "PINKAN_ISLAND": [145, 80],
               "SUNBURST_ISLAND": [350, 88], "NAVEL_ISLAND": [123, 142], "SHAMOUTI_ISLAND": [339, 170],
               "TROVITA_ISLAND": [92, 179], "KUMQUAT_ISLAND": [124, 252], "PUMMELO_ISLAND": [185, 277]},
    "ORRE": {"PHENAC_CITY": [201, 245], "PYRITE_TOWN": [326, 231], "GATEON_PORT": [112, 214],
             "AGATE_VILLAGE": [96, 131], "REALGAM_TOWER": [374, 99]},
    "DECOLORE": {"HONEY_ISLAND": [41, 38], "SCALCHOP_ISLAND": [223, 73], "GRAND_SPECTRALA_ISLAND": [109, 177],
                 "TOROM_ISLAND": [309, 261], "PALADIN_ISLAND": [392, 219]},
}
SQUARE = 16  # Essentials town-map grid


def norm(s):
    s = str(s).lower().replace("é", "e").replace("vermillion", "vermilion")
    return re.sub(r"[^a-z0-9]", "", s)


def map_file(n):
    hits = [f for f in os.listdir(PICS) if f.lower() == f"mapregion{n}.png"]
    return os.path.join(PICS, hits[0])


def townmap_points():
    """{region index: [(x, y, name)]} from PBS/townmap.txt (grid squares)."""
    out, cur = {}, None
    for line in open(os.path.join(JOURNEYS, "PBS", "townmap.txt"), encoding="utf-8-sig"):
        m = re.match(r"\[(\d+)\]", line.strip())
        if m:
            cur = int(m.group(1))
            continue
        m = re.match(r'Point=(\d+),(\d+),"([^"]*)"', line.strip())
        if m and cur is not None:
            out.setdefault(cur, []).append((int(m.group(1)), int(m.group(2)), m.group(3)))
    return out


def markers(img):  # used to find the squares while placing by hand
    """Centres of the town squares (red) and special places (blue) on a map."""
    w, h = img.get_size()
    hit = set()
    for x in range(w):
        for y in range(h):
            r, g, b, a = img.get_at((x, y))
            if (r > 200 and g < 150 and b < 150) or (b > 200 and r < 140 and g < 170):
                hit.add((x, y))
    seen, out = set(), []
    for p in hit:
        if p in seen:
            continue
        stack, blob = [p], []
        seen.add(p)
        while stack:
            x, y = stack.pop()
            blob.append((x, y))
            for n in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if n in hit and n not in seen:
                    seen.add(n)
                    stack.append(n)
        if len(blob) >= 12:
            xs, ys = [q[0] for q in blob], [q[1] for q in blob]
            out.append(((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2))
    return out


def main():
    pygame.init()
    data = json.load(open("assets/map_points.json", encoding="utf-8"))
    prog = {}
    for f in glob.glob("assets/*_area_data.json"):
        prog.update(json.load(open(f, encoding="utf-8")).get("STORY_PROGRESSION", {}))
    sub = {k: v for v, keys in data.get("sub_views", {}).items() for k in keys}

    def view_of(key):
        if key in sub:
            return sub[key]
        a = prog.get(key) or {}
        r = str(a.get("region") or "KANTO").upper()
        if a.get("subregion") == "SEVII":
            return "SEVII"
        return r

    os.makedirs(OUT, exist_ok=True)
    os.makedirs(PREVIEW, exist_ok=True)
    tm = townmap_points()
    region_maps = {}
    for view, n in MAPS.items():
        src = map_file(n)
        dst = os.path.join(OUT, f"{view.lower()}.png")
        shutil.copyfile(src, dst)
        img = pygame.image.load(src)
        keys = [k for k in data["points"] if view_of(k) == view]
        pts = {}
        marks = markers(img)
        if n in tm:  # Journeys' own points, by name
            by_name = {}
            for x, y, name in tm[n]:
                by_name.setdefault(norm(name), []).append((x, y))
            for k in keys:
                a = prog.get(k, {})
                for cand in (a.get("route_name", ""), k.replace("_", " ")):
                    sq = by_name.get(norm(cand))
                    if sq:
                        x, y = sq[len(sq) // 2]  # a long route: its middle square
                        x, y = x * SQUARE + SQUARE // 2, y * SQUARE + SQUARE // 2
                        near = [m for m in marks if (m[0] - x) ** 2 + (m[1] - y) ** 2 < 24 ** 2]
                        if near:  # onto the middle of its town square
                            x, y = min(near, key=lambda m: (m[0] - x) ** 2 + (m[1] - y) ** 2)
                        pts[k] = [round(x), round(y)]
                        break
        for k, xy in ASSIGN.get(view, {}).items():
            if k in keys:
                pts[k] = list(xy)
        region_maps[view] = {"file": f"region_maps/{view.lower()}.png", "points": pts}
        # a preview to check by eye
        pv = pygame.transform.scale(img, (img.get_width() * 2, img.get_height() * 2))
        font = pygame.font.SysFont("arial", 11, bold=True)
        for k, (x, y) in pts.items():
            town = (prog.get(k) or {}).get("area_type") == "town"
            pygame.draw.circle(pv, (255, 255, 255) if town else (30, 30, 30), (x * 2, y * 2), 5)
            pv.blit(font.render(((prog.get(k) or {}).get("route_name") or k)[:16], True, (0, 0, 0)), (x * 2 + 6, y * 2 - 6))
        pygame.image.save(pv, os.path.join(PREVIEW, f"{view.lower()}.png"))
        print(f"{view:9} map {n:2}: {len(pts)}/{len(keys)} areas placed")
    data["region_maps"] = region_maps
    json.dump(data, open("assets/map_points.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
