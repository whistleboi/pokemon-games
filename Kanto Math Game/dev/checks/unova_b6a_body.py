# Unova batch 6a (11-24): Route 6 (Cheren and HM03 Surf in the Season Research Lab, the Deerling gift, Cobalion and Rood
# on the west bridge, the rest house, two Hidden Grottoes), Chargestone Cave (its mouth, 1F, B1F, B2F: Bianca, the
# floating stones you push, N's voice, the Nugget pair), Mistralton Cave (1F, 2F, the Guidance Chamber: dark till Flash,
# the boulders on their holes, Cobalion after the Champion).
#   bash dev/checks/run.sh unova_b6a
import json
from src.states.overworld import CityState, PlayState


fails = []


def check(c, m):
    print(("   ok  " if c else "   FAIL ") + m)
    if not c:
        fails.append(m)


g.dungeon_routes = True; g.walk_towns = True; g.player_character = "nate"
flags = story.story_flags
flags["unova_version"] = "BLACK_2"; story.starting_region = "UNOVA"
NEW = ("UNOVA_ROUTE_6", "CHARGESTONE_CAVE_ENTRANCE", "CHARGESTONE_CAVE", "CHARGESTONE_CAVE_B1F", "CHARGESTONE_CAVE_B2F",
       "MISTRALTON_CAVE", "MISTRALTON_CAVE_2F", "GUIDANCE_CHAMBER")
for a in NEW + ("DRIFTVEIL_CITY",):
    flags["visited_" + a] = True
story.badges["UNOVA"] = ["BASIC", "TOXIC", "INSECT", "BOLT", "QUAKE"]
flags["b2_quake_badge"] = True; flags["b2_frigate_done"] = True; flags["b2_mom_talk"] = True
story.inventory["HM_STRENGTH"] = 1
said = []
tmaps = json.load(open("assets/town_maps.json", encoding="utf-8"))
prog = json.load(open("assets/unova_area_data.json", encoding="utf-8"))
SP = prog["STORY_PROGRESSION"]


exec(open("dev/checks/unova_lib.py", encoding="utf-8").read())   # (settle, heard, town, _opts, walked: shared, Checks C5)


def go(dx, dy, times=1, n=40):
    for _ in range(times):
        ds = g.current_state
        if hasattr(ds, "try_move"):
            ds.try_move(dx, dy)
        else:
            ds.step(dx, dy)
        settle(n)
    return g.current_state


def talk(st, label):
    spot = next((k for k, o in st.people.items() for c in _opts(o)
                 if isinstance(c, dict) and str(c.get("text", "")).rstrip() == label and st._shown(c)), None)
    if spot is None:
        return False
    said.clear(); st._talk(spot); settle(60)
    return True


def room_person(area, room, label):
    return next((c for o in tmaps[area]["rooms"][room].get("people") or [] for c in _opts(o)
                 if isinstance(c, dict) and str(c.get("text", "")).rstrip() == label), None)


print("1) the places: walked, their trainers and wild Pokemon from the file")
for a in NEW:
    check(a in tmaps, f"{a} is walked")
for a, n in (("UNOVA_ROUTE_6", 8), ("CHARGESTONE_CAVE", 6), ("CHARGESTONE_CAVE_B1F", 3), ("CHARGESTONE_CAVE_B2F", 4),
             ("MISTRALTON_CAVE", 2), ("MISTRALTON_CAVE_2F", 2)):
    check(len(SP[a]["trainer_pool"]) == n, f"{a}: Black 2's {n} trainers")
for a in NEW:
    if a != "CHARGESTONE_CAVE_ENTRANCE":
        check(bool(SP[a].get("wild_tables")), f"{a}: its own wild Pokemon")
for a in ("CHARGESTONE_CAVE", "CHARGESTONE_CAVE_B1F", "CHARGESTONE_CAVE_B2F", "MISTRALTON_CAVE", "MISTRALTON_CAVE_2F", "GUIDANCE_CHAMBER"):
    check(SP[a].get("phenomena") == "dust", f"{a}: dust clouds")
corky = next(t for t in SP["CHARGESTONE_CAVE"]["trainer_pool"] if t["name"] == "Ace Trainer Corky")
check((corky.get("battle_options") or {}).get("double"), "Ace Trainer Corky's Triple Battle is a double battle (Jordan 11-19)")
check(set(SP["UNOVA_ROUTE_6"]["wild_tables"]) == {"SPRING", "SUMMER", "AUTUMN", "WINTER"}, "Route 6's Pokemon by season")
check(not SP["UNOVA_ROUTE_6"].get("route_menu") and "area_boss" not in SP["MISTRALTON_CAVE"],
      "no menu-era buttons; Cobalion isn't the cave's menu boss any more")

print("2) Driftveil <-> Route 6")
ds = walked("UNOVA_ROUTE_6", (61, 53))
go(1, 0, 3)
check(story.current_area_key == "DRIFTVEIL_CITY", f"Route 6's east end leads into Driftveil ({story.current_area_key})")
for k in ("b2_drift_arrival", "b2_rood_battled", "b2_rood_talk", "b2_drift_clay_out", "b2_drift_zorua"):
    flags[k] = True   # (Driftveil's own story done: its scenes don't hold you)
st = town("DRIFTVEIL_CITY", (1, 21), face=(-1, 0)); settle(600); st = g.current_state
st.step(-1, 0); settle(120); st = g.current_state
if story.current_area_key == "DRIFTVEIL_CITY":
    st.step(-1, 0); settle(300)
check(story.current_area_key == "UNOVA_ROUTE_6", f"Driftveil's west road leads onto Route 6 ({story.current_area_key})")

print("3) Route 6: Cheren and the lab (HM03 Surf), the Deerling gift, the rest house")
flags.pop("b2_r6_cheren", None); flags.pop("b2_r6_surf", None); story.inventory.pop("HM_SURF", None)
ds = walked("UNOVA_ROUTE_6", (43, 21))
go(-1, 0, 1, 900)
check(flags.get("b2_r6_cheren") and "weather" in heard(), "Cheren outside the lab: 'Can you come with me?'")
st = town("UNOVA_ROUTE_6", (6, 6), "lab", (0, -1))
talk(st, "Cheren")
check(story.inventory.get("HM_SURF", 0) >= 1 and flags.get("b2_r6_surf"), "Cheren gives HM03 Surf in the lab")
team0 = len(story.player_team)
talk(st, "Scientist with the Deerling")
check(flags.get("b2_r6_deerling") and any(int(getattr(p, "id", 0)) == 585 and int(getattr(p, "level", 0)) == 30
                                          for p in list(story.player_team) + [p for p in story.pc_pokemon if p]),
      "the rare Deerling, Lv 30")
_d = next((p for p in list(story.player_team) + [p for p in story.pc_pokemon if p] if int(getattr(p, "id", 0)) == 585), None)
_ev = next(c for o in tmaps["UNOVA_ROUTE_6"]["rooms"]["lab"]["people"] for c in _opts(o) if isinstance(c, dict) and (c.get("event") or {}).get("gift_pokemon") == 585)
check(_ev["event"].get("gift_ability") == "hidden" and _ev["event"].get("gift_no_shiny") and _d is not None
      and not getattr(_d, "is_shiny", False), f"its Hidden Ability, Serene Grace, and never Shiny (slot {getattr(_d, 'ability_slot', None)})")
st = town("UNOVA_ROUTE_6", (10, 7), "house", (0, -1))
talk(st, "Girl in the rest house")
check(story.inventory.get("SHINY_STONE", 0) >= 1, "the girl's Shiny Stone")
woman = room_person("UNOVA_ROUTE_6", "house", "Woman by the table")
check(woman and woman["event"].get("heal"), "the woman in the rest house heals your team")

print("4) Route 6: Cobalion on the west bridge, Rood")
flags.pop("b2_r6_cobalion", None)
ds = walked("UNOVA_ROUTE_6", (7, 14))
go(0, -1, 1, 1500)
check(flags.get("b2_r6_cobalion") and "Cobalion" in heard(), "Cobalion leaps down; Rood and the old man")
for g_ in ("grotto", "grotto2"):
    check(g_ in tmaps["UNOVA_ROUTE_6"].get("rooms", {}), f"Route 6's Hidden Grotto ({g_})")

print("5) Chargestone Cave: in from Route 6; Bianca; the floating stones; N's voice")
ds = walked("UNOVA_ROUTE_6", (7, 1))
go(0, -1, 2)
check(story.current_area_key == "CHARGESTONE_CAVE_ENTRANCE", f"north from Route 6 to the cave's mouth ({story.current_area_key})")
ds = walked("CHARGESTONE_CAVE_ENTRANCE", (11, 20))
go(0, -1, 2)
check(story.current_area_key == "CHARGESTONE_CAVE", f"into Chargestone Cave ({story.current_area_key})")
flags.pop("b2_charge_bianca", None)
ds = walked("CHARGESTONE_CAVE", (7, 51))
go(0, -1, 1, 1500)
check(flags.get("b2_charge_bianca") and "Bianca" in heard() and "push" in heard(), "Bianca: push the floating stones!")
cc = tmaps["CHARGESTONE_CAVE"]
check(len(cc.get("stones") or []) == 10 and not any("_110_" in o["k"] for o in cc["roofs"].get("_objects") or []),
      f"1F's ten floating stones are stones you push, not the map's fixed models ({len(cc.get('stones') or [])})")
pushed = None
for cx, cy in cc.get("stones") or []:   # (stand off a stone's edge and walk into it: the 3 x 3 slides that way)
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        frm = (cx - 2 * dx, cy - 2 * dy)
        row = cc["art"][frm[1]] if 0 <= frm[1] < len(cc["art"]) else ""
        if not (0 <= frm[0] < len(row)) or row[frm[0]] not in '."':
            continue
        flags.pop("stones_CHARGESTONE_CAVE_0", None)
        ds = walked("CHARGESTONE_CAVE", frm)
        if tuple(getattr(getattr(ds, "run", None), "player", (0, 0))) != frm:
            continue
        go(dx, dy, 1, 60)
        now = flags.get("stones_CHARGESTONE_CAVE_0")
        if isinstance(now, list) and [cx, cy] not in [list(t) for t in now]:
            pushed = ((cx, cy), (dx, dy), [t for t in now if list(t) not in (cc.get("stones") or [])])
            break
    if pushed:
        break
check(pushed, f"walk into a floating stone: it slides on, and stays moved ({pushed})")
flags.pop("b2_charge_voice", None)
ds = walked("CHARGESTONE_CAVE", (44, 41))
go(1, 0, 1, 1200)
check(flags.get("b2_charge_voice") and "save Pokemon" in heard(), "a voice by the bridge: 'I have to go...'")

print("6) Chargestone's floors: 1F <-> B1F (three ways), B1F <-> B2F; out to Mistralton")
for door, there in (((53, 5), (39, 5)), ((20, 42), (9, 42)), ((64, 50), (47, 50))):   # (the file's own pairs)
    art = cc["art"]
    side = next(((door[0] - dx, door[1] - dy, dx, dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
                 if art[door[1] - dy][door[0] - dx] in '."'), None)
    ds = walked("CHARGESTONE_CAVE", side[:2])
    go(side[2], side[3], 1, 60)
    pl = tuple(getattr(getattr(g.current_state, "run", None), "player", (0, 0)))
    check(story.current_area_key == "CHARGESTONE_CAVE_B1F" and abs(pl[0] - there[0]) + abs(pl[1] - there[1]) <= 2,
          f"1F's stairs at {door} land by B1F's {there}, as the file pairs them ({story.current_area_key} {pl})")
check(tmaps["CHARGESTONE_CAVE"]["exits"].get("^") == "MISTRALTON_CITY", "1F's north-east exit leads to Mistralton City")
ds = walked("CHARGESTONE_CAVE_B1F", (28, 8))
go(-1, 0, 2)
check(story.current_area_key == "CHARGESTONE_CAVE_B2F", f"B1F's stairs down to B2F ({story.current_area_key})")
st = walked("CHARGESTONE_CAVE_B1F", (26, 53))
nug = (story.inventory.get("NUGGET", 0), story.inventory.get("BIG_NUGGET", 0))
gifts = [c for o in tmaps["CHARGESTONE_CAVE_B1F"]["people"] for c in _opts(o) if isinstance(c, dict) and "Nugget" in c.get("text", "")]
check({c["event"]["gift_item"] and list(c["event"]["gift_item"])[0] for c in gifts} == {"NUGGET", "BIG_NUGGET"},
      "the Nugget Man and Nugget Boy: a Nugget and a Big Nugget")

print("7) Mistralton Cave: dark; its boulders on their holes; the Guidance Chamber and Cobalion")
ds = walked("UNOVA_ROUTE_6", (59, 9))
go(1, 0, 2)
check(story.current_area_key == "MISTRALTON_CAVE", f"Route 6's east cave mouth: Mistralton Cave ({story.current_area_key})")
for a in ("MISTRALTON_CAVE", "MISTRALTON_CAVE_2F", "GUIDANCE_CHAMBER"):
    check(tmaps[a].get("dark"), f"{a} is dark till Flash")
ds = walked("MISTRALTON_CAVE", (2, 6))
check(getattr(ds, "recipe", {}).get("dark_radius") or getattr(ds, "recipe", {}).get("fog"),
      "in the dark the cave shows only a small light round you (main 11-24: dark_radius; was fog)")
check(tmaps["MISTRALTON_CAVE"]["art"][17][5] == "b", "1F: the boulder waits on the hole south")
check(tmaps["MISTRALTON_CAVE"]["exits"].get(">") == "CLAY_TUNNEL" and tmaps["MISTRALTON_CAVE"]["barred"][0]["until"]["flag_condition"] == "beat_unova_champion",
      "Clay Tunnel's door: shut (still being dug) till the Champion")
gc = tmaps["GUIDANCE_CHAMBER"]
cob = next((c for o in gc["people"] for c in _opts(o) if isinstance(c, dict) and c.get("action") == "BOSS"), None)
check(cob and cob["boss"]["id"] == 638 and cob["boss"]["level"] == 45 and "beat_unova_champion" in cob["condition"],
      "Cobalion in the Guidance Chamber after the Champion, Lv 45")
flags.pop("beat_unova_champion", None)
ds = walked("GUIDANCE_CHAMBER", (16, 26))
check("Cobalion" not in [str(getattr(m, "payload", "")) for m in getattr(getattr(ds, "run", None), "floor", None).movers]
      if hasattr(ds, "run") else True, "no Cobalion before the Champion")

print("8) the Journal")
missions = {m["id"]: m for m in prog["JOURNAL_MISSIONS"]}
check("b2_m30" in missions and missions["b2_m30"]["completed_flag"] == "b2_r6_surf", "the Journal sends you to Cheren at the lab")
check("b2_m31" in missions and missions["b2_m31"]["target"] == "CHARGESTONE_CAVE", "then through Chargestone Cave")
flags.pop("b2_r6_surf", None); flags["b2_frigate_done"] = True
main = [m["id"] for m in story.get_active_missions() if m["type"] == "MAIN"]
check("b2_m30" in main, f"after the Frigate: b2_m30 is the story step ({main})")
flags["b2_r6_surf"] = True
flags.pop("visited_MISTRALTON_CITY", None)
main = [m["id"] for m in story.get_active_missions() if m["type"] == "MAIN"]
check("b2_m31" in main, f"after Surf: b2_m31 ({main})")

for f_ in fails:
    print("  -", f_)
print(f"##### {len(fails)} failures")
