
from src.states import overworld as ow
from src.states.battle import WildBattleState
fails = 0


def check(c, m):
    global fails
    print(("   ok  " if c else "   FAIL ") + m)
    fails += 0 if c else 1


g.data.save = lambda *a, **k: None
prog = g.loader.area_data["STORY_PROGRESSION"]
HAUNTS = ["KANTO_POKEMON_TOWER", "BURNED_TOWER", "HOENN_MT_PYRE", "OLD_CHATEAU", "CELESTIAL_TOWER", "LOST_HOTEL",
          "THRIFTY_MEGAMART", "CROWN_OLD_CEMETERY", "DALIZAPA_PASSAGE", "LOST_CAVE", "SPECTRALA_WOODS"]

print("1) the form")
raw = g.loader.fetch_specific(10501)
check(raw["name"] == "BLACK FOG" and raw["img"] and raw["types"] == ["GHOST", "POISON"], f"{raw['name']} {raw['types']}")

print("2) every haunted place")
# (Walked regions' haunts are played on their maps: walk up to the Black Fog (legacy menu clear, Step 5, 11-24); the menu
#  regions' (Kalos, Alola, Galar, Paldea, Decolore) keep their route menu's boss button.)
exec(open("dev/checks/walk_lib.py", encoding="utf-8").read())
WALKED = {"BURNED_TOWER", "HOENN_MT_PYRE", "OLD_CHATEAU", "CELESTIAL_TOWER", "LOST_CAVE"}
# (KANTO_POKEMON_TOWER stays on the menu: its Black Fog is the route menu's stairs ambush (zone_ambush), which the walked
#  tower has no way to meet - recorded in LEGACY_MENU_AUDIT.md and sent to Kanto's inbox, 11-24.)
KNOWN = {"CELESTIAL_TOWER": "Unova's rebuilt Celestial Tower lost its Black Fog (route_menu): sent to Unova's inbox 11-24"}
story.balls_left = 20
story.player_team = [mk(150)]; story.player_team[0].level = 100
for key in HAUNTS:
    opt = next((o for o in prog[key].get("route_menu") or [] if o.get("text") == "THE BLACK FOG"), None)
    # (the Pokemon Tower's comes as an ambush on its stairs: zone_ambush, 11-02)
    boss = opt["boss"] if opt else (prog[key].get("zone_ambush") or {}).get("boss")
    if not boss:
        if key in KNOWN:
            print(f"   KNOWN {key}: {KNOWN[key]}")
            continue
        check(False, f"{key}: no Black Fog")
        continue
    flag = boss["victory_flag"]
    story.story_flags.pop(flag, None)
    if key in WALKED:
        st = walk_route(key, None)
        w = walk_meet(st, "THE BLACK FOG", fight=False)
        if w is None:
            check(False, f"{key}: the Black Fog isn't on the map")
            continue
    else:
        g.walk_towns = g.dungeon_routes = False
        story.current_area_key = key
        st = ow.PlayState(g)
        g.change_state(st)
        st.action_challenge_boss(dict(boss, lines=None))
        g.walk_towns = g.dungeon_routes = True
    b = g.current_state
    ok = isinstance(b, WildBattleState) and b.opponent_pokemon.id == 10501 and b.no_catch
    b.trigger_outro(True)
    check(ok and story.story_flags.get(flag) and b.phase == "OUTRO",
          f"{key}: Lv {b.opponent_pokemon.level} Black Fog, can't be caught, gone once beaten{' (walked up to)' if key in WALKED else ''}")
    if key in WALKED and ok:
        story.story_flags[flag] = True
        check(walk_who(walk_route(key, None), "THE BLACK FOG") is None, f"...{key}: gone from the map once beaten")
print("FAILURES:", fails)
