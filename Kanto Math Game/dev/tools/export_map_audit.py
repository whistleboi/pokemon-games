"""The map audit (Jordan, 11-08): every drawn map beside the picture it was made from, in one folder.

    python dev/tools/export_map_audit.py

Writes dev/map_audit/ (not kept in git; run this again any time):
    index.html                 open this: each map beside its original, a tick and notes for each
    <REGION>/<AREA>/built.png  (or built_1.png, built_2.png... for each floor)
    <REGION>/<AREA>/original_*.png  copies of its source pictures
The originals stay where they are: assets/backgrounds/<region>/ and dev/reference/maps/. To build a new map, see
dev/builders/town_maps/MAPPING_GUIDE.md."""
import glob
import html
import json
import os
import shutil
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
GAME = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, GAME)
import pygame  # noqa: E402

OUT = os.path.join(GAME, "dev", "map_audit")
BG = os.path.join(GAME, "assets", "backgrounds")
REF = os.path.join(GAME, "dev", "reference", "maps")
TILE = 56  # (the game's own drawing size; saved at half that, and the page shows them at 16 px a tile, the originals' scale)
K, R = "kanto/", "kanto/routes/"
# area -> its source pictures (under assets/backgrounds, or "ref:" for dev/reference/maps). Routes are found by name.
SOURCES = {
    "PALLET_TOWN": [K + "pallet_city.png"], "VIRIDIAN_CITY": [K + "viridian_city.png"], "PEWTER_CITY": [K + "pewter_city.png"],
    "CERULEAN_CITY": [K + "cerulean_city.png"], "BILLS_HOUSE": [K + "bills_city.png"], "VERMILLION_CITY": [K + "vermillion_city.png"],
    "LAVENDER_TOWN": [K + "lavender_city.png", "ref:Lavender_Town_FRLG.png", "ref:example 2 towers levender.png"],
    "CELADON_CITY": [K + "celadon_city.png"], "FUCHSIA_CITY": [K + "fuchsia_city.png"], "SAFFRON_CITY": [K + "saffron_city.png"],
    "CINNABAR_ISLAND": ["ref:Cinnabar_Island_FRLG.png", K + "cinnabar_city.png"], "POWER_PLANT": [K + "power_plant.png", R + "power_plant.png"],
    "INDIGO_PLATEAU": [K + "indigo_city.png"], "MT_MOON": [K + "mt_moon.png", R + "mt_moon.png"],
    "ROCK_TUNNEL": [K + "rock_tunnel.png", R + "rock_tunnel.png"], "ROCKET_HIDEOUT": [K + "rocket_hideout.png"],
    "SILPH_CITY": [K + "silph_co.png", K + "silph_city.png"], "SAFARI_ZONE": ["ref:KantoSafari.png", K + "safari_zone.png", R + "safari_zone.png"],
    "SEAFOAM_ISLANDS": [K + "seafoam_island.png"], "DIGGLETT_CAVE": [K + "diglett_cave.png", R + "digglett_cave.png"],
    "VICTORY_ROAD": [K + "victory_road.png"], "CERULEAN_CAVE": [K + "cerulean_cave.png", R + "cerulean_cave.png"],
    "UNDERGROUND_PATH": [K + "underground_city.png"], "KANTO_ROUTE_10_SOUTH": [R + "kanto_route_10.png"],
    "KANTO_POKEMON_TOWER": [K + f"pokemon_tower_{i}.png" for i in range(1, 5)],
    "VIRIDIAN_FOREST": ["ref:journeys_viridian_forest.png"], "KANTO_SS_ANNE": ["ref:journeys_ss_anne_decks.png", "ref:journeys_ss_anne_ship.png"],
}
JOURNEYS = {"journeys_viridian_forest.png": 326, "journeys_ss_anne_decks.png": 345, "journeys_ss_anne_ship.png": 349}
FROM_DOWNLOADS = ("Lavender_Town_FRLG.png", "example 2 towers levender.png", "Cinnabar_Island_FRLG.png", "KantoSafari.png")
PAGE = """<!doctype html><meta charset=utf-8><title>Map audit</title>
<style>
body{font:15px sans-serif;background:#1c2233;color:#eef;margin:0;padding:16px}h1{margin:0 0 4px}h2{margin:28px 0 8px;color:#ffd76e}
nav{position:sticky;top:0;background:#1c2233;padding:8px 0;z-index:2}input[type=search]{padding:6px;width:240px}
section{background:#2a3250;border-radius:10px;padding:12px;margin:12px 0}.head{display:flex;gap:16px;align-items:center;flex-wrap:wrap}
.head b{font-size:18px}.row{display:flex;gap:14px;overflow-x:auto;padding-top:10px;align-items:flex-start}
figure{margin:0;flex:none}figcaption{font-size:13px;color:#b9c3e6;margin-bottom:4px}img{image-rendering:pixelated;background:#111;display:block;max-width:none}
textarea{width:260px;height:32px}section.ok{outline:2px solid #58c47a}.none{color:#ff9a8a}
</style>
<h1>Map audit</h1><p>Each map beside the picture it was made from. Ticks and notes stay in this browser.</p>
<nav><input type=search id=q placeholder="Find a map"> <label><input type=checkbox id=todo> only not ticked</label> <span id=count></span></nav>
%s
<script>
var S=document.querySelectorAll('section');function load(k){try{return JSON.parse(localStorage.getItem('audit:'+k)||'{}')}catch(e){return{}}}
function save(k,v){try{localStorage.setItem('audit:'+k,JSON.stringify(v))}catch(e){}}
function count(){var n=0;S.forEach(function(s){if(s.classList.contains('ok'))n++});document.getElementById('count').textContent=n+' of '+S.length+' checked'}
function show(){var q=document.getElementById('q').value.toUpperCase().replace(/ /g,'_'),t=document.getElementById('todo').checked;S.forEach(function(s){s.style.display=(s.id.indexOf(q)>=0&&!(t&&s.classList.contains('ok')))?'':'none'})}
S.forEach(function(s){var d=load(s.id),c=s.querySelector('.tick'),n=s.querySelector('textarea');c.checked=!!d.ok;n.value=d.note||'';s.classList.toggle('ok',c.checked);
function w(){save(s.id,{ok:c.checked,note:n.value});s.classList.toggle('ok',c.checked);count();}c.onchange=w;n.oninput=w;});
document.getElementById('q').oninput=show;document.getElementById('todo').onchange=show;count();
</script>"""


def keep_downloads():
    """The pictures that only ever lived in Downloads: kept with the project."""
    os.makedirs(REF, exist_ok=True)
    home = os.path.expanduser("~/Downloads")
    for n in FROM_DOWNLOADS:
        if not os.path.exists(os.path.join(REF, n)) and os.path.exists(os.path.join(home, n)):
            shutil.copy(os.path.join(home, n), os.path.join(REF, n))


def render_journeys():
    """Sources that only exist inside the fan game: one picture each, once."""
    todo = {n: m for n, m in JOURNEYS.items() if not os.path.exists(os.path.join(REF, n))}
    if not todo:
        return
    sys.path.insert(0, os.path.join(GAME, "dev", "builders"))
    try:
        import render_journeys_backgrounds as J
        game = J.Journeys(J.JOURNEYS)
        for name, mid in todo.items():
            img = next(x for x in game.render(mid) if isinstance(x, pygame.Surface))
            pygame.image.save(pygame.transform.scale(img, (img.get_width() // 2, img.get_height() // 2)), os.path.join(REF, name))
    except Exception as e:  # (the fan game isn't on this computer)
        print("Journeys pictures skipped:", e)


def region_of(area):
    return "JOHTO" if area.startswith(("JOHTO", "NEW_BARK", "CHERRYGROVE")) else "KANTO"


def sources(area, region):
    listed = SOURCES.get(area)
    if listed is None:
        low = area.lower().replace("_town", "").replace("_city", "")
        r = region.lower()
        listed = [p[len(BG) + 1:].replace("\\", "/") for p in glob.glob(os.path.join(BG, r, "**", "*.png"), recursive=True)
                  if os.path.basename(p)[:-4] in (area.lower(), low + "_city", low)]
    out = []
    for s in listed:
        path = os.path.join(REF, s[4:]) if s.startswith("ref:") else os.path.join(BG, s)
        if os.path.exists(path):
            out.append(path)
    return out


def main():
    from src.dungeon import art
    pygame.init()
    pygame.display.set_mode((8, 8))
    keep_downloads()
    render_journeys()
    maps = json.load(open(os.path.join(GAME, "assets", "town_maps.json"), encoding="utf-8-sig"))
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    groups, missing = {}, []
    for area, m in maps.items():
        region = region_of(area)
        folder = os.path.join(OUT, region, area)
        os.makedirs(folder)
        floors = [f["art"] for f in m["floors"]] if m.get("floors") else [m["art"]]
        built = []
        for i, grid in enumerate(floors):
            name = "built.png" if len(floors) == 1 else f"built_{i + 1}.png"
            full = art.surface(grid, m.get("buildings", {}), TILE, m.get("roofs"), m.get("theme"))
            pygame.image.save(pygame.transform.scale(full, (full.get_width() // 2, full.get_height() // 2)), os.path.join(folder, name))
            built.append((name, len(grid[0]), len(grid)))
        originals = []
        for path in sources(area, region):
            name = "original_" + os.path.basename(path).replace(" ", "_")
            shutil.copy(path, os.path.join(folder, name))
            originals.append(name)
        if not originals:
            missing.append(area)
        figs = "".join(f"<figure><figcaption>Ours{'' if len(built) == 1 else f' {i + 1}'} ({w} x {h})</figcaption><img loading=lazy width={w * 16} src='{region}/{area}/{n}'></figure>"
                       for i, (n, w, h) in enumerate(built))
        figs += "".join(f"<figure><figcaption>{html.escape(n[9:])}</figcaption><img loading=lazy src='{region}/{area}/{n}'></figure>" for n in originals)
        none = "" if originals else " <span class=none>no original on file</span>"
        groups.setdefault(region, []).append(
            f"<section id='{area}'><div class=head><b>{area}</b>{none}<label><input type=checkbox class=tick> looks right</label><textarea placeholder='notes'></textarea></div><div class=row>{figs}</div></section>")
    body = "".join(f"<h2>{r.title()} ({len(s)})</h2>" + "".join(s) for r, s in groups.items())
    open(os.path.join(OUT, "index.html"), "w", encoding="utf-8").write(PAGE % body)
    print(len(maps), "maps ->", OUT)
    print("no original:", missing)


if __name__ == "__main__":
    main()
