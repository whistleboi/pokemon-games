
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
story.balls_left = 20
for key in HAUNTS:
    story.current_area_key = key
    st = ow.PlayState(g)
    g.change_state(st)
    opt = next((o for o in prog[key]["route_menu"] if o.get("text") == "THE BLACK FOG"), None)
    if not opt:
        check(False, f"{key}: no Black Fog")
        continue
    flag = opt["boss"]["victory_flag"]
    story.story_flags.pop(flag, None)
    st.action_challenge_boss(dict(opt["boss"], lines=None))
    b = g.current_state
    ok = isinstance(b, WildBattleState) and b.opponent_pokemon.id == 10501 and b.no_catch
    b.trigger_outro(True)
    check(ok and story.story_flags.get(flag) and b.phase == "OUTRO",
          f"{key}: Lv {b.opponent_pokemon.level} Black Fog, can't be caught, gone once beaten")
print("FAILURES:", fails)
