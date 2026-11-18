
# Every form that can be seen on a map has its own following-Pokemon sheet (Jordan, 11-17: "any form variation
# or regional form change should have an accompanying overworld sprite"), normal and shiny, and the game picks it:
# for a Pokemon in your party (meta_id + form), for a map's bare id (a boss's 9103, "mon:2008") and a species
# with a form (201 "b", 6 "mega_x"). The forms that still need art are listed in kanto_handoff/FOLLOWER_FORMS.md.
import json
from src.states.overworld import dungeon as dn
from src.states.overworld.dungeon import DungeonState, follower_names

fails = 0


def check(c, m):
    global fails
    print(("   ok  " if c else "   FAIL ") + m)
    fails += 0 if c else 1


BASE = os.path.join(g.assets.assets_dir, "dungeon", "followers")
fm = g.loader.area_data.get("FORM_MAP", {})
SAME_LOOK = {"shadow", "single", "own_tempo"}            # (looks like its species in the games: the species' sheet is right)
SAME_IDS = {7005, 3025}                                   # (Silvally Normal; Nown)
NEEDS_ART = {6002, 6003, 7003, 7004, 8003, 10501, 3022, 3023, 3044, 3049}   # (no walking art anywhere yet: FOLLOWER_FORMS.md)
NEEDS_ART_MEGA = {"154", "160", "227", "358", "380", "478", "500", "530", "545", "560", "604", "609", "652", "655", "658",
                  "668", "670", "689", "691", "718", "780", "870"}
NEEDS_ART_UNOWN = {"k"}
CRYSTAL = 9201                                            # (Crystal Onix: its sheet is another worker's, 95_crystal.png)


class _Mon:
    def __init__(self, pid, form="normal", shiny=False, meta=None, gender=None):
        self.id, self.form, self.is_shiny, self.gender = pid, form, shiny, gender
        if meta is not None:
            self.meta_id = meta


def first(mon, shiny):
    for n in follower_names(g, mon):
        for sub in (("shiny", "") if shiny else ("",)):
            if os.path.isfile(os.path.join(BASE, sub, n + ".png")):
                return (sub + "/" if sub else "") + n
    return None


def own(mon, species):
    """(normal, shiny) sheet names the game picks, and whether both are the form's own (not the species')."""
    a, b = first(mon, False), first(mon, True)
    return a, b, a not in (None, str(species)) and b not in (None, "shiny/" + str(species), str(species))


print("1) every FORM_MAP form: its own sheet, from a party Pokemon and from a bare id")
gaps, checked = [], 0
for k, m in sorted(fm.items(), key=lambda kv: int(kv[0])):
    fid, sp, form = int(k), int(m.get("id", 0)), str(m.get("form", "normal")).lower()
    if form in SAME_LOOK or fid in SAME_IDS or fid == CRYSTAL:
        continue
    checked += 1
    for mon, how in ((_Mon(fid, form, meta=sp), "party"), (_Mon(fid), "bare id")):
        a, b, ok = own(mon, sp)
        if fid in NEEDS_ART:
            gaps.append(f"{fid} {m.get('name')}")
            print(f"   gap  {fid} {m.get('name')} ({how}): needs art, species sheet for now ({a})")
            break
        check(ok, f"{fid} {m.get('name')} ({how}): {a} / {b}")

print("2) Pinkan and Valencia: every one recoloured, normal and shiny")
orange = json.load(open(os.path.join(g.assets.assets_dir, "orange_area_data.json"), encoding="utf-8"))["FORM_MAP"]
for k, m in sorted(orange.items()):
    if m.get("form") in ("pinkan", "valencia"):
        n = f"{m['id']}_{m['form']}"
        check(os.path.isfile(os.path.join(BASE, n + ".png")) and os.path.isfile(os.path.join(BASE, "shiny", n + ".png")),
              f"{k} {m['name']}: {n}.png + shiny")

print("3) Megas / Primals by the form the battle gives (mega_x...) and Unown's letters")
mf = json.load(open(os.path.join(g.assets.assets_dir, "mega_forms.json"), encoding="utf-8"))
for sp, forms in sorted(mf.items(), key=lambda kv: int(kv[0])):
    for f in forms:
        if sp in NEEDS_ART_MEGA:
            continue
        a, b, ok = own(_Mon(int(sp), f["form"]), sp)
        check(ok, f"{f['name']} ({sp} {f['form']}): {a} / {b}")
for letter in "bcdefghijlmnopqrstuvwxyz":   # (K: needs art)
    a, b, ok = own(_Mon(201, letter), 201)
    check(ok, f"Unown {letter.upper()}: {a} / {b}")
for f in ("question", "exclamation"):
    a, b, ok = own(_Mon(201, f), 201)
    check(ok, f"Unown {f}: {a} / {b}")

print("4) the game's own loader picks the sheet (a party Pinkan Butterfree; a map boss's bare 3003; Alolan by form)")
loaded = []
party_pinkan = mk(9103)
_load = pygame.image.load
pygame.image.load = lambda p, *a: (loaded.append(os.path.basename(os.path.dirname(p)) + "/" + os.path.basename(p)) if isinstance(p, str) else None, _load(p, *a))[1]


class _Stub:
    game = g
    _sprite = DungeonState._sprite
    _trainer_scale = lambda self: 2
    _jumbo = lambda self, c: c


try:
    for mon, want in ((party_pinkan, "followers/12_pinkan.png"), (_Mon(3003), "followers/6_mega_y.png"),
                      (_Mon(50, "alolan"), "followers/2008.png"), (_Mon(9517, shiny=True), "shiny/130_valencia.png"),
                      (_Mon(479, "heat"), "followers/479_heat.png"), (_Mon(25, gender="F"), "followers/25_female.png")):
        loaded.clear()
        img = DungeonState._follower_img(_Stub(), mon, (0, 1))
        check(img is not None and loaded and loaded[0] == want, f"{getattr(mon, 'display_name', mon.id)} {mon.form}: {loaded[:1]}")
finally:
    pygame.image.load = _load

print(f"   ({checked} FORM_MAP forms checked; still needing art: {len(set(gaps))})")
print("FAILURES:", fails)
